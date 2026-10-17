# SPDX-License-Identifier: AGPL-3.0-only
"""Who may use Encryptor, the same way everywhere:

- AI apps on this computer (stdio) are the person's own apps: the app that started Encryptor may use it.
- AI apps on the web version connect with OAuth: the person types their passphrase once and ticks which vaults the
  app may use, and whether it may change files (PassphraseOAuth). Tokens are kept only as fingerprints.
- The control center (the person's own pages) uses a sign-in cookie (Sessions): on the web version after the
  passphrase, on a computer through a one-time link that Encryptor opens in the person's browser (never shown to
  the AI). Five wrong passphrases from one address pause it for 15 minutes; fifty from anywhere pause all.
Single person, no accounts.
"""

from __future__ import annotations

import hmac
import json
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    RegistrationError,
    TokenError,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from .store import check_passphrase, private_write, read_json, token_key

MIN_PASSPHRASE = 8
SCOPE = "encryptor"
FAIL_WINDOW, FAIL_LIMIT, FAIL_LIMIT_ALL = 15 * 60, 5, 50


def passphrase_ok(passphrase: str, cfg: dict) -> bool:
    """LOGIN_HASH (from set-passphrase) wins; LOGIN_PASSPHRASE is the plain one for hosting dashboards."""
    if cfg.get("LOGIN_HASH"):
        return check_passphrase(passphrase, cfg["LOGIN_HASH"])
    plain = cfg.get("LOGIN_PASSPHRASE", "")
    return bool(plain) and hmac.compare_digest(passphrase.encode(), plain.encode())


def public_url(cfg: dict) -> str:
    """PUBLIC_URL, or the address Render or Railway gives the app, or localhost."""
    if cfg.get("PUBLIC_URL"):
        return cfg["PUBLIC_URL"].rstrip("/")
    if cfg.get("RENDER_EXTERNAL_URL"):
        return cfg["RENDER_EXTERNAL_URL"].rstrip("/")
    if cfg.get("RAILWAY_PUBLIC_DOMAIN"):
        return f"https://{cfg['RAILWAY_PUBLIC_DOMAIN']}"
    return f"http://localhost:{cfg.get('PORT') or 8767}"


class Lockout:
    """Five wrong passphrases within 15 minutes from one address pause that address for 15 minutes, so someone
    guessing from elsewhere can't lock the owner out. Fifty from anywhere pause every sign-in, which still caps
    guessing from many addresses at once."""

    def __init__(self):
        self.failures: list[tuple[float, str]] = []

    def locked(self, ip: str = "") -> bool:
        cutoff = time.time() - FAIL_WINDOW
        self.failures = [f for f in self.failures if f[0] > cutoff]
        return (len(self.failures) >= FAIL_LIMIT_ALL
                or sum(1 for _, who in self.failures if who == ip) >= FAIL_LIMIT)

    def failed(self, ip: str = "") -> None:
        self.failures.append((time.time(), ip))


class PassphraseOAuth:
    """The AI app registers, the person types the passphrase and ticks its vaults, the app gets tokens."""

    ACCESS_TTL = 3600   # short-lived: a leaked key stops working within the hour
    REFRESH_TTL = 90 * 24 * 3600
    MAX_CLIENTS = 50   # registering is open to anyone, so keep the list from growing forever

    def __init__(self, public_url: str, redirect_hosts: list[str], path: Path, check, lockout: Lockout):
        """check(passphrase) -> bool."""
        self.public_url = public_url.rstrip("/")
        self.redirect_hosts = [h.lower() for h in redirect_hosts]
        self.path = path
        self.check = check
        self.lockout = lockout
        self.lock = threading.Lock()
        self.pending: dict[str, tuple[float, str, AuthorizationParams]] = {}
        self.codes: dict[str, AuthorizationCode] = {}
        data = read_json(path, {})
        self.clients = {k: OAuthClientInformationFull.model_validate(v) for k, v in data.get("clients", {}).items()}
        self.access = {k: AccessToken.model_validate(v) for k, v in data.get("access", {}).items()}
        self.refresh = {k: RefreshToken.model_validate(v) for k, v in data.get("refresh", {}).items()}
        # app -> {"vaults": [names ticked on the login page], "change": may it change files}
        self.grants: dict[str, dict] = data.get("grants", {})

    def save(self) -> None:
        now = time.time()
        self.access = {k: v for k, v in self.access.items() if not v.expires_at or v.expires_at > now}
        self.refresh = {k: v for k, v in self.refresh.items() if not v.expires_at or v.expires_at > now}
        private_write(self.path, json.dumps({
            "clients": {k: v.model_dump(mode="json") for k, v in self.clients.items()},
            "access": {k: v.model_dump(mode="json") for k, v in self.access.items()},
            "refresh": {k: v.model_dump(mode="json") for k, v in self.refresh.items()},
            "grants": self.grants,
        }, indent=1))

    def redirect_ok(self, uri) -> bool:
        p = urlparse(str(uri))
        host = (p.hostname or "").lower()
        if host in ("localhost", "127.0.0.1", "::1"):
            return p.scheme in ("http", "https")
        return p.scheme == "https" and any(host == h or host.endswith("." + h) for h in self.redirect_hosts)

    def app_name(self, client_id: str) -> str:
        client = self.clients.get(client_id)
        return app_label(client.client_name if client else "")

    async def get_client(self, client_id: str):
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        bad = [str(u) for u in (client_info.redirect_uris or []) if not self.redirect_ok(u)]
        if bad:
            raise RegistrationError("invalid_redirect_uri", f"Redirect not allowed: {', '.join(bad)}")
        with self.lock:
            cutoff = time.time() - 3600   # registrations that never logged in are forgotten after an hour
            for cid in [cid for cid, c in self.clients.items()
                        if (c.client_id_issued_at or 0) < cutoff and cid not in self.grants]:
                del self.clients[cid]
            while len(self.clients) >= self.MAX_CLIENTS:
                oldest = min(self.clients, key=lambda k: self.clients[k].client_id_issued_at or 0)
                del self.clients[oldest]
            self.clients[client_info.client_id] = client_info
            self.save()

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        if not self.redirect_ok(params.redirect_uri):
            raise AuthorizeError("invalid_request", "Redirect not allowed")
        req = secrets.token_urlsafe(24)
        with self.lock:
            self.pending = {k: v for k, v in self.pending.items() if v[0] > time.time()}
            self.pending[req] = (time.time() + 600, client.client_id, params)
        return f"{self.public_url}/login?req={req}"

    def describe(self, req: str) -> tuple[str, str] | None:
        """(app name, where the login goes back to) for a waiting login, shown on the login page."""
        entry = self.pending.get(req)
        if not entry or entry[0] < time.time():
            return None
        return self.app_name(entry[1]), urlparse(str(entry[2].redirect_uri)).hostname or "?"

    def complete_login(self, req: str, passphrase: str, vaults: list[str], change: bool, ip: str = "") -> str | None:
        """The redirect back to the app on success, None on a wrong passphrase. vaults: the names ticked."""
        if not vaults:
            raise ValueError("Tick at least one vault.")
        with self.lock:
            if self.lockout.locked(ip):
                raise PermissionError("Too many wrong tries. Wait 15 minutes.")
            entry = self.pending.get(req)
            if not entry or entry[0] < time.time():
                raise LookupError("This login link expired. Start the connection again in your AI app.")
            if not self.check(passphrase):
                self.lockout.failed(ip)
                return None
            del self.pending[req]
            _, client_id, params = entry
            self.grants[client_id] = {"vaults": sorted(set(vaults)), "change": bool(change), "since": time.time()}
            self.save()
            code = secrets.token_urlsafe(32)
            self.codes[code] = AuthorizationCode(
                code=code, scopes=params.scopes or [SCOPE], expires_at=time.time() + 300, client_id=client_id,
                code_challenge=params.code_challenge, redirect_uri=params.redirect_uri,
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                resource=params.resource, subject="owner")
        return construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)

    def set_grant(self, client_id: str, vaults: list[str], change: bool) -> None:
        with self.lock:
            if client_id in self.grants:
                self.grants[client_id].update(vaults=sorted(set(vaults)), change=bool(change))
                self.save()

    async def load_authorization_code(self, client, authorization_code: str):
        code = self.codes.get(authorization_code)
        if code and code.client_id == client.client_id and code.expires_at > time.time():
            return code
        return None

    def issue(self, client_id: str, scopes: list[str], resource: str | None) -> OAuthToken:
        now = int(time.time())
        access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        a_key, r_key = token_key(access), token_key(refresh)
        self.access[a_key] = AccessToken(token=a_key, client_id=client_id, scopes=scopes,
                                         expires_at=now + self.ACCESS_TTL, resource=resource, subject="owner")
        self.refresh[r_key] = RefreshToken(token=r_key, client_id=client_id, scopes=scopes,
                                           expires_at=now + self.REFRESH_TTL, resource=resource, subject="owner")
        self.save()
        return OAuthToken(access_token=access, token_type="Bearer", expires_in=self.ACCESS_TTL,
                          refresh_token=refresh, scope=" ".join(scopes))

    async def exchange_authorization_code(self, client, authorization_code: AuthorizationCode) -> OAuthToken:
        with self.lock:
            if self.codes.pop(authorization_code.code, None) is None:
                raise TokenError("invalid_grant", "Code already used")
            return self.issue(client.client_id, authorization_code.scopes, authorization_code.resource)

    async def load_refresh_token(self, client, refresh_token: str):
        tok = self.refresh.get(token_key(refresh_token))
        if tok and tok.client_id == client.client_id and (not tok.expires_at or tok.expires_at > time.time()):
            return tok.model_copy(update={"token": refresh_token})
        return None

    async def exchange_refresh_token(self, client, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
        with self.lock:
            if self.refresh.pop(token_key(refresh_token.token), None) is None:
                raise TokenError("invalid_grant", "Refresh token already used")
            return self.issue(client.client_id, scopes or refresh_token.scopes, refresh_token.resource)

    async def load_access_token(self, token: str):
        tok = self.access.get(token_key(token))
        if tok and (not tok.expires_at or tok.expires_at > time.time()) and self.for_us(tok.resource) \
                and tok.client_id in self.grants:
            return tok.model_copy(update={"token": token})
        return None

    def for_us(self, resource) -> bool:
        """A key issued for a different server (another 'resource') is never accepted here."""
        if not resource:
            return True
        r = str(resource).rstrip("/").lower()
        return r in (self.public_url.lower(), f"{self.public_url.lower()}/mcp")

    async def revoke_token(self, token) -> None:
        self.disconnect(token.client_id, forget=False)

    def disconnect(self, client_id: str, forget: bool = True) -> None:
        """Log an app out. forget=True also removes it and its vault choice (the control center's Disconnect)."""
        with self.lock:
            self.access = {k: v for k, v in self.access.items() if v.client_id != client_id}
            self.refresh = {k: v for k, v in self.refresh.items() if v.client_id != client_id}
            if forget:
                self.clients.pop(client_id, None)
                self.grants.pop(client_id, None)
            self.save()


def app_label(name: str) -> str:
    """An app's own name, as shown to the person; one that starts like "You" is marked, so no app can pose as them."""
    name = " ".join((name or "").split())[:80] or "An AI app"
    return f"An AI app called {name}"[:80] if name.casefold().startswith("you") else name


def describe_agent(ua: str) -> str:
    """A short, plain name for a browser from its User-Agent ("Safari on Mac"); never the whole string."""
    ua = ua or ""
    browser = next((name for key, name in (("Edg/", "Edge"), ("OPR/", "Opera"), ("Brave", "Brave"), ("Firefox/", "Firefox"),
                                           ("Chrome/", "Chrome"), ("Safari/", "Safari")) if key in ua), "A browser")
    system = next((name for key, name in (("iPhone", "iPhone"), ("iPad", "iPad"), ("Android", "Android"),
                                          ("Mac OS X", "Mac"), ("Windows", "Windows"), ("Linux", "Linux")) if key in ua), "")
    return f"{browser} on {system}" if system else browser


class Sessions:
    """Control center sign-ins: a random cookie, kept only as a fingerprint, each with its own form token.
    Normal sign-ins end when the program stops; "remember this device" ones last 90 days and are kept in a file
    (path) on the web version. A new passphrase (mark() changes) signs everyone out. log_path keeps 7 days of
    sign-in attempts: when, how, which browser, from where, right or wrong. Never a passphrase."""

    TTL = 12 * 3600
    REMEMBER = 90 * 24 * 3600
    LINK_TTL = 5 * 60
    LOG_DAYS = 7

    def __init__(self, mark=lambda: "", path: Path | None = None, log_path: Path | None = None):
        self.mark = mark
        self.path, self.log_path = path, log_path
        self.lock = threading.Lock()
        now = time.time()
        self.items: dict[str, dict] = {k: v for k, v in (read_json(path, {}) if path else {}).items()
                                       if v.get("expires", 0) > now}
        self.links: dict[str, float] = {}   # one-time sign-in links (on a computer), as fingerprints
        self.log: list[dict] = read_json(log_path, []) if log_path else []

    def _save(self) -> None:
        if self.path:
            private_write(self.path, json.dumps({k: v for k, v in self.items.items() if v.get("remember")}))

    def record(self, ok: bool, how: str, agent: str = "", ip: str = "") -> None:
        with self.lock:
            cutoff = time.time() - self.LOG_DAYS * 86400
            self.log = [e for e in self.log if e["time"] > cutoff][-300:]
            self.log.append({"time": time.time(), "ok": ok, "how": how, "agent": describe_agent(agent), "ip": ip[:64]})
            if self.log_path:
                private_write(self.log_path, json.dumps(self.log))

    def new(self, remember: bool = False, agent: str = "", ip: str = "") -> str:
        with self.lock:
            now = time.time()
            self.items = {k: v for k, v in self.items.items() if v["expires"] > now}
            token = secrets.token_urlsafe(32)
            self.items[token_key(token)] = {
                "expires": now + (self.REMEMBER if remember else self.TTL), "csrf": secrets.token_urlsafe(24),
                "pp": self.mark(), "remember": bool(remember), "since": now, "seen": now,
                "agent": describe_agent(agent), "ip": ip[:64]}
            self._save()
            return token

    def get(self, token: str) -> dict | None:
        if not token:
            return None
        s = self.items.get(token_key(token))
        if s and s["expires"] > time.time() and hmac.compare_digest(s["pp"], self.mark()):
            if time.time() - s.get("seen", 0) > 60:
                s["seen"] = time.time()
                if s.get("remember"):
                    with self.lock:
                        self._save()
            return s
        return None

    def end(self, token: str) -> None:
        with self.lock:
            self.items.pop(token_key(token), None)
            self._save()

    def devices(self, token: str) -> list[dict]:
        """Signed-in browsers, newest first; "id" is a short public handle, "this" marks the asking browser."""
        mine = token_key(token or "")
        now = time.time()
        out = [{"id": k[:16], "this": k == mine, **{f: v.get(f) for f in ("since", "seen", "agent", "ip", "remember")}}
               for k, v in self.items.items() if v["expires"] > now]
        return sorted(out, key=lambda d: d["seen"] or 0, reverse=True)

    def end_device(self, device_id: str, token: str = "", others: bool = False) -> int:
        """Sign out one browser by its handle, or every browser but this one (others=True)."""
        mine = token_key(token or "")
        with self.lock:
            gone = [k for k in self.items if (others and k != mine) or (not others and device_id and k.startswith(device_id))]
            for k in gone:
                del self.items[k]
            self._save()
            return len(gone)

    def new_link(self) -> str:
        """A one-time code for /signin/<code>: works once, for 5 minutes."""
        with self.lock:
            now = time.time()
            self.links = {k: v for k, v in self.links.items() if v > now}
            code = secrets.token_urlsafe(32)
            self.links[token_key(code)] = now + self.LINK_TTL
            return code

    def use_link(self, code: str) -> bool:
        with self.lock:
            expires = self.links.pop(token_key(code or ""), 0)
            return expires > time.time()
