# SPDX-License-Identifier: AGPL-3.0-only
"""The local unlock page: a tiny web server on 127.0.0.1 only, started with the MCP server.

GET  /unlock/<code>            the form (the code works once, for 5 minutes)
POST /unlock/<code>            password, how long, read only
GET  /vault/<status code>      what's open and for how long
POST /vault/<status code>/lock lock now
GET  /vault/<status code>/files/<folder>/   browse a folder
GET  /vault/<status code>/open/<file>       view a text file, picture or PDF in the browser (sandboxed)
GET  /vault/<status code>/get/<file>        download a file (decrypted)
POST /vault/<status code>/mount, /unmount   show the vault in Finder (or the file manager), or remove it
The status code is a long random secret shown only to the person, in their browser, after unlocking.
Requests must name this server's own address (no other host names: protection against DNS rebinding), and form
posts must come from this server's own pages.
"""

from __future__ import annotations

import hmac
import mimetypes
import threading
import time
from pathlib import Path
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import changes, pages
from .vault import keys
from .auth import Lockout, Sessions
from .unlock import UnlockManager, UnlockRefused

MAX_FORM = 8 * 1024
SIGNIN_APP = "You, signing in"   # an unlock started on the sign-in page: unlocking also signs the person in
VIEWABLE = {"image/png", "image/jpeg", "image/gif", "image/webp"}   # PDFs: download only (no viewer in the sandbox)
FILE_HEADERS = {   # decrypted files can't run anything, load anything, or reach these pages
    "Content-Security-Policy": "sandbox; default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; "
                               "frame-ancestors 'none'",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def _kind(name: str, data: bytes) -> str | None:
    """The type to show a file as in the browser, or None to only offer the download."""
    guess = mimetypes.guess_type(name)[0] or ""
    if guess in VIEWABLE:
        return guess
    if guess.startswith("text/") or guess in ("application/json", "application/xml", "") or name.endswith((".md", ".csv")):
        if b"\x00" not in data[:8192]:
            try:
                data.decode("utf-8")
                return "text/plain; charset=utf-8"
            except UnicodeDecodeError:
                return None
    return None


def _cookies(headers: dict) -> dict[str, str]:
    jar = SimpleCookie()
    try:
        jar.load(headers.get("cookie", ""))
    except Exception:
        return {}
    return {k: m.value for k, m in jar.items()}


class Center:
    """The control center: the person's own pages (all vaults, unlock and lock, settings, connected apps).

    hosted=False (a computer): sign-in only through a one-time link Encryptor opens in the person's browser, or from
    the page of a vault the person just unlocked. hosted=True (a server): sign-in with the passphrase.
    The other callables come from server.py: journal_for(session), view() -> settings dict, save(kind, form) -> note.
    """

    def __init__(self, journal_for, view, save, hosted: bool = False, check=None, lockout=None, provider=None,
                 secure: bool = False, mark=lambda: "", sessions_file=None, log_file=None, lock_all=None,
                 health=None, fingerprints=None, readlog=None, log_read=None):
        self.journal_for, self.view, self.save = journal_for, view, save
        self.hosted, self.check, self.provider, self.secure = hosted, check, provider, secure
        self.lockout = lockout or Lockout()
        self.sessions = Sessions(mark, sessions_file, log_file)
        self.lock_all = lock_all   # locks every vault (and removes Finder mounts); from server.py
        self.health = health       # session -> (findings, note): the health check plus fingerprints
        self.fingerprints = fingerprints
        self.readlog = readlog       # session -> ReadLog (private to the person)
        self.log_read = log_read     # (session, path, how, purpose, who)
        self.cookie = ("__Host-encryptor" if secure else "encryptor_center")

    def session(self, headers: dict) -> dict | None:
        return self.sessions.get(_cookies(headers).get(self.cookie, ""))

    def set_cookie(self, token: str, max_age: int | None = None) -> dict:
        parts = [f"{self.cookie}={token}", "Path=/", "HttpOnly", "SameSite=Strict"]
        if self.secure:
            parts.append("Secure")
        if max_age is not None:
            parts.append(f"Max-Age={max_age}")
        return {"Set-Cookie": "; ".join(parts)}

    def sign_in(self, headers: dict | None = None, remember: bool = False, how: str = "link") -> tuple[int, dict, str]:
        headers = headers or {}
        agent, ip = headers.get("user-agent", ""), headers.get("x-client-ip", "")
        self.sessions.record(True, how, agent, ip)
        token = self.sessions.new(remember, agent, ip)
        return 303, {"Location": "/", **self.set_cookie(token, self.sessions.REMEMBER if remember else None)}, ""


class Site:
    """Everything the pages need: the vaults (manager), Finder mounts (mounts, a computer only) and the control
    center (center). One instance serves a computer (LocalPages) or a server (server.serve)."""

    def __init__(self, manager: UnlockManager, base: str, mounts=None, center: Center | None = None):
        self.manager, self.base, self.mounts, self.center = manager, base, mounts, center

    # ------------------------------------------------ a vault's own page (gated by its secret status code)

    def vault_view(self, s, note: str = "") -> dict:
        m, mounts = self.manager, self.mounts
        view = {"name": s.vault.name, "status_code": s.status_code, "read_only": s.read_only, "keep": s.keep,
                "app": s.app, "ends_at": time.strftime("%H:%M", time.localtime(s.expires)),
                "idle_minutes": int(m.idle_for(s.vault) // 60), "left_minutes": m.seconds_left(s) // 60,
                "finder": mounts.label() if mounts and mounts.available() else None,
                "mounted": mounts.where(s.vault.name) if mounts else "", "note": note,
                "center": self.center is not None, "changes": [], "trash": [],
                "center_link": "/" if self.center is None or self.center.hosted else f"/vault/{s.status_code}/center",
                "health": getattr(s, "health", None), "reads": None}
        if self.center is not None:
            j = self.center.journal_for(s)
            in_trash = {r["trash"] for r in j.trash_items()}
            for r in j.records(15):
                view["changes"].append({
                    "id": r["id"], "when": time.strftime("%d %b %H:%M", time.localtime(r["time"])),
                    "action": r["action"], "path": r["path"], "to": r.get("to", ""), "app": r["app"],
                    "purpose": r.get("purpose", ""), "undone": bool(r.get("undone_by")),
                    "undoable": not s.read_only and not r.get("undone_by")
                                and r["action"] not in ("undo", "empty_trash")
                                and (r["action"] != "trash" or r.get("trash") in in_trash)})
            if self.center.readlog:
                try:
                    entries, verdict = self.center.readlog(s).read(30)
                    view["reads"] = {"entries": entries, "verdict": verdict}
                except Exception:
                    view["reads"] = {"entries": [], "verdict": "The read log can't be opened."}
            for r in j.trash_items():
                view["trash"].append({"id": r["trash"], "change": r["id"], "path": r["path"], "kind": r.get("kind", "file"),
                                      "when": time.strftime("%d %b %H:%M", time.localtime(r["time"])), "app": r["app"]})
        return view

    def vault_page(self, method: str, parts: list[str], form: dict, headers: dict | None = None):
        m, mounts = self.manager, self.mounts
        s = m.by_status_code(parts[1])
        if s is None:
            return 404, {}, pages.message("Locked", "This vault is locked.", ok=True, center=self.center is not None)
        action = parts[2] if len(parts) > 2 else ""
        rel = "/".join(unquote(p) for p in parts[3:])
        if method == "POST" and action == "lock" and len(parts) == 3:
            if mounts:
                mounts.unmount(s.vault.name)
            m.lock(s.vault.name, "locked on its page")
            return 200, {}, pages.message("Locked", f"{s.vault.name} is locked. The keys are gone from memory.",
                                          ok=True, center=self.center is not None)
        if method == "POST" and action in ("mount", "unmount") and len(parts) == 3 and mounts:
            m.use(s.vault.name, person=True)
            try:
                if action == "mount":
                    note = f"Open in {mounts.label()}, under Locations."
                    mounts.mount(s)
                else:
                    mounts.unmount(s.vault.name)
                    note = f"Removed from {mounts.label()}."
            except Exception as exc:   # a plain-words reason from mount.py
                note = str(exc)
            return 200, {}, pages.vault_page(self.vault_view(s, note))
        if method == "POST" and action in ("health", "repair") and len(parts) == 3 and self.center is not None:
            from .vault import health
            m.use(s.vault.name, person=True)
            def run_check():
                return self.center.health(s) if self.center.health else (health.check(s.tree), "")
            if action == "repair":
                if s.read_only:
                    return 403, {}, pages.vault_page(self.vault_view(s, "This vault is open read only."))
                found = [f for f in run_check()[0] if f.fix]
                if form.get("confirm") != "yes":
                    return 200, {}, pages.confirm_change({
                        "csrf": "", "action": f"/vault/{s.status_code}/repair", "back": f"/vault/{s.status_code}",
                        "title": f"Repair {s.vault.name}?", "button": f"Yes, repair {len(found)}",
                        "fields": {}, "facts": [(f.kind, f.where) for f in found[:8]],
                        "lines": [f.fix for f in found[:8]] + ["Only safe repairs are made; nothing is deleted "
                                                               "except leftover temporary files."]})
                done = []
                for f in found:
                    try:
                        if f.kind == "ChangedElsewhere" and self.center.fingerprints:
                            n = self.center.fingerprints(s).record_all()
                            done.append(f"Remembered the vault as it is now ({n} files).")
                            continue
                        done.append(health.repair(s.tree, f))
                    except Exception as exc:
                        done.append(f"Not repaired ({f.where}): {exc}")
                m._event(s.vault.name, f"repaired {len(found)} problem(s) on the control center")
                s.health = (time.time(), run_check()[0])
                return 200, {}, pages.vault_page(self.vault_view(s, " ".join(done) or "Nothing to repair."))
            found, note = run_check()
            s.health = (time.time(), found)
            n = len(found)
            return 200, {}, pages.vault_page(self.vault_view(
                s, ("Healthy: nothing wrong found." if not n else f"Found {n} thing(s) to look at, below.")
                + (f" {note}" if note else "")))
        if method == "POST" and action in ("undo", "purge") and len(parts) == 3 and self.center is not None:
            m.use(s.vault.name, person=True)
            if s.read_only:
                return 403, {}, pages.vault_page(self.vault_view(s, "This vault is open read only."))
            j = self.center.journal_for(s)
            try:
                if action == "undo":
                    rec = j.undo(form.get("change", ""), "You (control center)", "")
                    note = f"Undone: {rec['did']}."
                else:
                    if form.get("confirm") != "yes":
                        return 400, {}, pages.vault_page(self.vault_view(
                            s, "Tick the box to confirm. Deleting for good can't be undone."))
                    rec = j.empty_trash(form.get("item", ""), "You (control center)", "")
                    note = f"Deleted {len(rec['removed'])} item(s) for good."
                m._event(s.vault.name, f"{action} on the control center")
            except keys.VaultError as exc:
                note = str(exc)
            return 200, {}, pages.vault_page(self.vault_view(s, note))
        if method == "GET" and action == "center" and len(parts) == 3 and self.center and not self.center.hosted:
            return self.center.sign_in(headers, how="vault page")   # just unlocked here: on a computer, that's enough
        if method == "GET" and not action and len(parts) == 2:
            return 200, {}, pages.vault_page(self.vault_view(s))
        if method != "GET" or action not in ("files", "open", "get"):
            return 404, {}, pages.message("Not found", "There's nothing here.")
        m.use(s.vault.name, person=True)   # looking counts as using the vault
        try:
            e = s.tree.resolve(changes.clean(rel))
        except keys.VaultError as exc:
            return 404, {}, pages.message("Not found", str(exc))
        if action == "files":
            if e.kind != "dir":
                return 404, {}, pages.message("Not a folder", f"'{rel}' isn't a folder.")
            rows = []
            for item in s.tree.list_dir(e.dir_id):
                if e.dir_id == b"" and item.name.casefold() == changes.META:
                    continue
                date = time.strftime("%Y-%m-%d %H:%M", time.localtime(item.stored.stat().st_mtime))
                if item.kind == "file":
                    size = _size(s.tree.file_size(item))
                    viewable = (mimetypes.guess_type(item.name)[0] or "") in VIEWABLE or _maybe_text(item.name)
                    rows.append((item.name, "file", size, date, viewable))
                else:
                    rows.append((item.name, item.kind, "", date, False))
            return 200, {}, pages.browse(s.vault.name, s.status_code, rel, rows)
        if e.kind != "file":
            return 404, {}, pages.message("Not a file", f"'{rel}' isn't a file.")
        data = s.tree.read_file(e)
        m._event(s.vault.name, f"{'viewed' if action == 'open' else 'downloaded'} {rel} on the browse page")
        if self.center and self.center.log_read:
            self.center.log_read(s, changes.clean(rel), "viewed" if action == "open" else "downloaded", "", "You")
        name = e.name
        if action == "open":
            kind = _kind(name, data)
            if kind is None:
                return 200, {}, pages.message("Can't show this here", f"'{name}' can't be shown in the browser. Download it instead.")
            return 200, {**FILE_HEADERS, "Content-Type": kind}, data
        ascii_name = name.encode("ascii", "replace").decode().replace('"', "_").replace("?", "_")
        return 200, {**FILE_HEADERS, "Content-Type": "application/octet-stream",
                     "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"}, data

    # ------------------------------------------------ the control center (gated by the sign-in cookie)

    def home_view(self, sess: dict, note: str = "") -> dict:
        m = self.manager
        m.sweep()
        rows = []
        for v in m.vaults.values():
            s = m.sessions.get(v.name.casefold())
            rows.append({"name": v.name, "mode": v.mode, "open": s is not None,
                         "read_only": bool(s and s.read_only) or v.mode == "read",
                         "status_code": s.status_code if s else "", "app": s.app if s else "",
                         "ends_at": time.strftime("%H:%M", time.localtime(s.expires)) if s else "",
                         "left_minutes": m.seconds_left(s) // 60 if s else 0})
        apps = []
        prov = self.center.provider
        if prov is not None:
            for cid, g in prov.grants.items():
                apps.append({"id": cid, "name": prov.app_name(cid), "vaults": g.get("vaults", []),
                             "change": g.get("change", False)})
        view = self.center.view()
        return {"vaults": rows, "csrf": sess["csrf"], "note": note, "hosted": self.center.hosted, "apps": apps,
                "read_only_all": view.get("read_only_all", False), "default": next(
                    (r["name"] for r in view.get("vaults", []) if r.get("default")), "")}

    def center_page(self, method: str, parts: list[str], form: dict, headers: dict) -> tuple[int, dict, str]:
        c, m = self.center, self.manager
        head = parts[0] if parts else ""
        if head == "signin":
            if len(parts) == 3 and parts[1] == "unlock" and method == "POST" and not c.hosted:
                try:
                    v = m.spec(unquote(parts[2]))   # never a hidden vault from here
                except UnlockRefused as exc:
                    return 404, {}, pages.signin(False, str(exc), self.signin_vaults())
                return 303, {"Location": f"/unlock/{m.request_unlock(v.name, SIGNIN_APP, '')}"}, ""
            if len(parts) == 2 and method == "GET" and not c.hosted:
                if c.sessions.use_link(parts[1]):
                    return c.sign_in(headers, how="one-time link")
                c.sessions.record(False, "expired link", headers.get("user-agent", ""), headers.get("x-client-ip", ""))
                return 410, {}, pages.signin(False, "This sign-in link expired or was already used.",
                                             self.signin_vaults())
            if len(parts) == 1 and c.hosted:
                if method == "GET":
                    return 200, {}, pages.signin(True)
                if c.lockout.locked():
                    return 429, {}, pages.signin(True, "Too many wrong tries. Wait 15 minutes.")
                if not c.check(form.get("passphrase", "")):
                    c.lockout.failed()
                    c.sessions.record(False, "passphrase", headers.get("user-agent", ""), headers.get("x-client-ip", ""))
                    time.sleep(1)   # slows down guessing
                    return 401, {}, pages.signin(True, "Wrong passphrase.")
                return c.sign_in(headers, remember=form.get("remember") == "yes", how="passphrase")
            return 404, {}, pages.message("Not found", "There's nothing here.")
        sess = c.session(headers)
        if sess is None:
            return 200 if head == "" else 401, {}, pages.signin(c.hosted, "", self.signin_vaults())
        if method == "POST" and not hmac.compare_digest(form.get("csrf", ""), sess["csrf"]):
            return 403, {}, pages.message("Not allowed", "This form is out of date. Reload the page and try again.")
        if head == "" and method == "GET":
            return 200, {}, pages.center_home(self.home_view(sess, sess.pop("flash", "")))
        if head == "signout" and method == "POST":
            c.sessions.end(_cookies(headers).get(c.cookie, ""))
            return 303, {"Location": "/", **c.set_cookie("", 0)}, ""
        if head == "vaults" and parts[1:] == ["lock-all"] and method == "POST":
            if c.lock_all:
                c.lock_all()
            else:
                m.lock_all("locked on the control center")
            return 200, {}, pages.center_home(self.home_view(sess, "Every vault is locked. The keys are gone from memory."))
        if head == "devices" and len(parts) == 3 and parts[2] == "signout" and method == "POST":
            token = _cookies(headers).get(c.cookie, "")
            n = c.sessions.end_device(parts[1], token, others=parts[1] == "others")
            return 303, {"Location": "/activity#devices"}, ""
        if head == "vaults" and len(parts) == 3 and method == "POST":
            name = unquote(parts[1])
            try:
                v = m.spec(name, person=True)
            except UnlockRefused as exc:
                return 404, {}, pages.center_home(self.home_view(sess, str(exc)))
            if parts[2] == "unlock":
                code = m.request_unlock(v.name, "You, from the control center", "", person=True)
                return 303, {"Location": f"/unlock/{code}"}, ""
            if parts[2] == "lock":
                if self.mounts:
                    self.mounts.unmount(v.name)
                m.lock(v.name, "locked on the control center")
                return 303, {"Location": "/"}, ""
        if head == "apps" and len(parts) == 3 and parts[2] == "disconnect" and method == "POST" and c.provider:
            c.provider.disconnect(unquote(parts[1]))
            return 303, {"Location": "/"}, ""
        if head == "activity" and len(parts) == 1 and method == "GET":
            token = _cookies(headers).get(c.cookie, "")
            return 200, {}, pages.activity({"csrf": sess["csrf"], "devices": c.sessions.devices(token),
                                            "log": list(reversed(c.sessions.log[-50:]))})
        if head == "about" and len(parts) == 1:
            note, error = "", ""
            if method == "POST":
                kind = form.get("kind", "")
                try:
                    note = c.save(kind, form) if kind in ("updates", "check_now") else ""
                except ValueError as exc:
                    error = str(exc)
            return 200, {}, pages.about({**c.view(), "csrf": sess["csrf"], "note": note, "error": error})
        if head == "settings" and len(parts) == 3 and parts[1] == "vault":
            return self.vault_settings(method, unquote(parts[2]), form, sess, headers)
        if head == "settings":
            note, error = "", ""
            if method == "POST":
                try:
                    note = c.save(form.get("kind", ""), form)
                except ValueError as exc:
                    error = str(exc)
            return (400 if error else 200), {}, self.settings_page(sess, headers, note, error)
        return 404, {}, pages.message("Not found", "There's nothing here.")

    def settings_page(self, sess: dict, headers: dict, note: str = "", error: str = "") -> str:
        c = self.center
        token = _cookies(headers).get(c.cookie, "")
        return pages.settings({
            **c.view(), "csrf": sess["csrf"], "note": note, "error": error, "hosted": c.hosted,
            "devices": c.sessions.devices(token), "log": list(reversed(c.sessions.log[-20:])),
            "mcp_url": f"{self.base}/mcp" if c.hosted else ""})

    def vault_settings(self, method: str, name: str, form: dict, sess: dict, headers: dict):
        c, m = self.center, self.manager
        note, error = "", ""
        if method == "POST":
            kind = form.get("kind", "")
            if kind in ("rename", "path", "remove") and form.get("confirm") != "yes":
                ask = self.double_check(kind, name, form, sess)
                if ask:
                    return 200, {}, ask
                error = "Fill in the new name or folder first."
            else:
                try:
                    note = c.save(kind, {**form, "name": name})
                except ValueError as exc:
                    error = str(exc)
                if kind == "rename" and not error:
                    name = (form.get("new_name") or "").strip()
                if kind == "remove" and not error:
                    if self.mounts:
                        self.mounts.unmount(name)
                    sess["flash"] = note   # shown once on Your vaults
                    return 303, {"Location": "/"}, ""
        row = next((v for v in c.view()["vaults"] if v["name"].casefold() == name.casefold()), None)
        if row is None:
            return 404, {}, pages.message("Not found", f"No vault called {name!r}.", center=True)
        s = m.sessions.get(row["name"].casefold())
        try:
            from .vault import keys as _keys
            cfg = _keys.read_vault_config_unverified(Path(row["path"], "vault.cryptomator").read_bytes())[0]
            fmt = f"Cryptomator vault format 8, {cfg.cipher_combo}"
        except Exception:
            fmt = "Unreadable here (is the folder still there?)"
        return (400 if error else 200), {}, pages.vault_settings({
            "vault": row, "csrf": sess["csrf"], "note": note, "error": error, "open": s is not None,
            "app": s.app if s else "", "status_code": s.status_code if s else "", "format": fmt,
            "idle_all": int(m.idle // 60), "setup_file": c.view().get("setup_file", "")})

    def double_check(self, kind: str, name: str, form: dict, sess: dict) -> str | None:
        """The confirmation page for a critical change to a vault (rename, move, remove), or None if it can't
        be asked yet (an empty field)."""
        row = next((v for v in self.center.view()["vaults"] if v["name"].casefold() == name.casefold()), None)
        if row is None:
            return None
        action = f"/settings/vault/{quote(row['name'])}"
        base = {"csrf": sess["csrf"], "action": action}
        if kind == "rename":
            new = (form.get("new_name") or "").strip()
            if not new:
                return None
            return pages.confirm_change({**base, "title": f"Rename {row['name']}?", "button": "Yes, rename",
                                         "fields": {"kind": "rename", "new_name": new},
                                         "facts": [("Now", row["name"]), ("New name", new)],
                                         "lines": ["Your AI apps will know it by the new name.",
                                                   "If it's open, it locks first."]})
        if kind == "path":
            new = (form.get("path") or "").strip()
            if not new:
                return None
            return pages.confirm_change({**base, "title": f"Change {row['name']}'s folder?", "button": "Yes, change folder",
                                         "fields": {"kind": "path", "path": new},
                                         "facts": [("Now", pages.home(row["path"])), ("New folder", new)],
                                         "lines": ["Nothing is copied or moved: the vault entry just points at the new "
                                                   "folder.", "If it's open, it locks first."]})
        return pages.confirm_change({**base, "title": f"Remove {row['name']}?", "button": "Yes, remove it",
                                     "fields": {"kind": "remove"},
                                     "facts": [("Folder", pages.home(row["path"]))],
                                     "lines": ["It comes off this list. The vault and its files stay where they are.",
                                               "AI apps can no longer ask for it. You can add it again anytime."]})

    # ------------------------------------------------ AI-app login (a server only)

    def app_login(self, method: str, form: dict, query: dict) -> tuple[int, dict, str]:
        prov = self.center.provider
        req = form.get("req") or query.get("req", "")
        info = prov.describe(req)
        names = [v.name for v in self.manager.vaults.values() if v.mode != "hidden"]
        if method == "GET" or info is None:
            return (200 if info else 410), {}, pages.app_login(info, req, names)
        chosen = [n for n in form.get("vault_list", []) if n in names]
        try:
            target = prov.complete_login(req, form.get("passphrase", ""), chosen, form.get("change") == "yes")
        except (PermissionError, LookupError, ValueError) as exc:
            return (400 if isinstance(exc, ValueError) else 403), {}, pages.app_login(info, req, names, str(exc))
        if target is None:
            time.sleep(1)
            return 401, {}, pages.app_login(info, req, names, "Wrong passphrase.")
        return 302, {"Location": target, "Referrer-Policy": "no-referrer"}, ""

    # ------------------------------------------------ every request

    def handle(self, method: str, path: str, form: dict, headers: dict, query: dict | None = None):
        """Framework-free: (status, extra headers, body)."""
        parts = [p for p in path.split("?")[0].split("/") if p]
        theme = _cookies(headers).get("theme", "")
        pages.THEME.set("dark" if theme == "dark" else "light")
        pages.HERE.set(path if _safe_next(path) else "/")
        if method == "POST" and not same_origin(headers, self.base):
            return 403, {}, pages.message("Not allowed", "This form didn't come from this page.")
        if parts == ["theme"] and method == "POST":   # light <-> dark, remembered by this browser for a year
            nxt = form.get("next", "/")
            new = "light" if theme == "dark" else "dark"
            secure = "; Secure" if self.base.startswith("https://") else ""
            return 303, {"Location": nxt if _safe_next(nxt) else "/",
                         "Set-Cookie": f"theme={new}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax{secure}"}, ""
        if len(parts) == 2 and parts[0] == "unlock":
            return self.unlock_page(method, parts[1], form, headers)
        if len(parts) >= 2 and parts[0] == "vault":
            return self.vault_page(method, parts, form, headers)
        if parts[:1] == ["login"] and self.center and self.center.provider:
            return self.app_login(method, form, query or {})
        if self.center is not None and (not parts or parts[0] in ("signin", "signout", "vaults", "settings", "apps", "devices", "activity", "about")):
            return self.center_page(method, parts, form, headers)
        return 404, {}, pages.message("Not found", "There's nothing here.")

    def signin_vaults(self) -> list[str]:
        """Vaults offered on a computer's sign-in page (never hidden ones; none on a server)."""
        if self.center is None or self.center.hosted:
            return []
        return [v.name for v in self.manager.vaults.values() if v.mode != "hidden"]

    def unlock_page(self, method: str, code: str, form: dict, headers: dict | None = None):
        m = self.manager
        req = m.describe(code)
        if req is None:
            return 410, {}, pages.message("Link expired", "This unlock link has expired or was already used. "
                                          "Ask your AI app to unlock the vault again.", center=self.center is not None)
        if method == "GET":
            return 200, {}, pages.unlock_form(code, req.vault, req.app, req.purpose, idle_minutes=int(m.idle // 60),
                                              center=self.center is not None)
        try:
            s = m.unlock(code, form.get("password", ""), form.get("keep", "lock"), form.get("read_only") == "yes")
        except UnlockRefused as exc:
            time.sleep(1)   # slows down guessing
            return 401, {}, pages.unlock_form(code, req.vault, req.app, req.purpose, str(exc),
                                              idle_minutes=int(m.idle // 60),
                                              center=self.center is not None)
        if req.app == SIGNIN_APP and self.center is not None and not self.center.hosted:
            return self.center.sign_in(headers or {}, how="vault password")   # in, with that vault open
        return 303, {"Location": f"/vault/{s.status_code}"}, ""


def _safe_next(path: str) -> bool:
    """A path on this server only (no other site, no header tricks)."""
    return (path.startswith("/") and not path.startswith("//") and len(path) < 2000
            and not any(c in path for c in "\\\r\n\t"))


def _maybe_text(name: str) -> bool:
    guess = mimetypes.guess_type(name)[0] or ""
    return guess.startswith("text/") or guess in ("application/json", "application/xml") or name.endswith((".md", ".csv"))


def _size(n: float) -> str:
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{int(n)} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)


def same_origin(headers: dict, base: str) -> bool:
    origin = headers.get("origin")
    if origin and origin != "null":
        return origin.rstrip("/") == base
    return headers.get("sec-fetch-site", "same-origin") in ("same-origin", "none")


class LocalPages:
    """The unlock page on 127.0.0.1, on a free port, in a background thread."""

    def __init__(self, manager: UnlockManager, port: int = 0, mounts=None, center: Center | None = None):
        self.manager = manager
        self.mounts = mounts
        self.center = center
        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "Encryptor"
            sys_version = ""

            def log_message(self, *args):   # nothing about requests goes to the console
                pass

            def _serve(self, method: str):
                headers = {k.lower(): v for k, v in self.headers.items()}
                headers["x-client-ip"] = "this computer"
                if headers.get("host") not in outer.allowed_hosts:
                    return self._send(421, {}, "Wrong address.")
                form = {}
                if method == "POST":
                    length = int(headers.get("content-length") or 0)
                    if length > MAX_FORM:
                        return self._send(413, {}, "Too large.")
                    raw = self.rfile.read(length).decode("utf-8", "replace")
                    parsed = parse_qs(raw, keep_blank_values=True)
                    form = {k: v[0] for k, v in parsed.items()}
                    form["vault_list"] = parsed.get("vault", [])
                url = urlparse(self.path)
                query = {k: v[0] for k, v in parse_qs(url.query).items()}
                status, extra, body = outer.site.handle(method, url.path, form, headers, query)
                self._send(status, extra, body)

            def _send(self, status: int, extra: dict, body: str | bytes):
                data = body if isinstance(body, bytes) else body.encode()
                self.send_response(status)
                for k, v in {**pages.HEADERS, "Content-Type": "text/html; charset=utf-8", **extra}.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._serve("GET")

            def do_POST(self):
                self._serve("POST")

        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.port = self.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.allowed_hosts = {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}
        self.site = Site(manager, self.base, mounts, center)
        threading.Thread(target=self.httpd.serve_forever, name="unlock-page", daemon=True).start()

    def unlock_url(self, code: str) -> str:
        return f"{self.base}/unlock/{code}"

    def signin_url(self) -> str:
        """A one-time sign-in link for the control center (opened in the person's browser, never given to the AI)."""
        return f"{self.base}/signin/{self.center.sessions.new_link()}"

    def close(self) -> None:
        self.httpd.shutdown()
