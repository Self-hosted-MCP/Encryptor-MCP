# SPDX-License-Identifier: AGPL-3.0-only
"""Unlocking and locking vaults. The password is typed by the person on a page or in a box, never in the chat.

1. The AI asks to unlock a vault (with a purpose). request_unlock() makes a one-time link code: it works once,
   for UNLOCK_LINK_TTL seconds, and carries no secret.
2. The person opens the page, types the password and chooses how long the vault stays open, and whether read only.
3. While open, the keys live only here, in memory. Every use counts as activity.
4. The vault locks when asked, after IDLE minutes without use, at the time chosen, at MAX_HOURS at the latest, or
   when this program stops. Locking overwrites the keys.
Wrong passwords slow down: five within 15 minutes lock that vault's unlock page for 15 minutes.
"""

from __future__ import annotations

import math
import secrets
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .vault import keys, tree

UNLOCK_LINK_TTL = 5 * 60
FAIL_WINDOW = 15 * 60
FAIL_LIMIT = 5
KEEP_CHOICES = {"15m": 15 * 60, "1h": 3600, "lock": None, "app": None}


class Locked(Exception):
    """The vault is locked; the message says how to unlock it."""


class UnlockRefused(Exception):
    """A plain-words reason the unlock didn't happen (expired link, lockout, wrong password...)."""


@dataclass
class VaultSpec:
    name: str
    path: Path
    mode: str = "full"          # full, read or hidden
    idle_minutes: float | None = None   # its own auto-lock time, or None for the one set for all vaults


@dataclass
class Request:
    vault: str
    app: str
    purpose: str
    created: float
    used: bool = False
    signin: bool = False   # started on the sign-in page: unlocking also signs the person in
    person: bool = False   # started by the person (sign-in page or control center), never by an app, whatever its name


@dataclass
class Session:
    vault: VaultSpec
    key: keys.Masterkey
    tree: tree.Tree
    read_only: bool
    keep: str
    opened: float
    expires: float          # the time chosen, or the hard limit
    last_used: float
    app: str
    purpose: str
    status_code: str = field(default_factory=lambda: secrets.token_urlsafe(24))
    journal: object = None      # changes.Journal, made on the first change
    health: object = None       # (time, findings) of the last health check
    fp: object = None           # fingerprints.Fingerprints, made on the first health check
    readlog: object = None      # readlog.ReadLog, made on the first read


class UnlockManager:
    def __init__(self, vaults: list[VaultSpec], idle_minutes: float = 10, max_hours: float = 12, clock=time.time):
        self.vaults = {v.name.casefold(): v for v in vaults}
        self.idle = idle_minutes * 60
        self.max_age = max_hours * 3600
        self.clock = clock
        self.lock_ = threading.RLock()
        self.requests: dict[str, Request] = {}
        self.sessions: dict[str, Session] = {}
        self.failures: dict[str, list[float]] = {}
        self.events: list[tuple[float, str, str]] = []   # (time, vault, what): for the log, never with secrets
        self.on_lock: list = []   # called with the vault name after it locks (in a thread): e.g. remove a mount

    # ------------------------------------------------------------ helpers

    def spec(self, name: str, person: bool = False) -> VaultSpec:
        """A vault by name. Hidden vaults exist only for the person (the control center), never for the AI."""
        v = self.vaults.get((name or "").casefold())
        if v is None or (v.mode == "hidden" and not person):
            raise UnlockRefused(f"No vault called {name!r}.")
        return v

    def set_vaults(self, vaults: list[VaultSpec]) -> None:
        """New vault list or modes (from the settings page). A vault that's gone locks; one now read only stays
        open read only; one now hidden stays open for the person only."""
        with self.lock_:
            self.vaults = {v.name.casefold(): v for v in vaults}
            for key, s in list(self.sessions.items()):
                v = self.vaults.get(key)
                if v is None or v.path != s.vault.path:
                    self.lock(s.vault.name, "locked: removed from the vault list") if v else self._drop(key)
                    continue
                s.vault = v
                if v.mode == "read":
                    s.read_only = True

    def _drop(self, key: str) -> None:
        s = self.sessions.pop(key, None)
        if s:
            s.key.wipe()
            self._event(s.vault.name, "locked: removed from the vault list")
            self._after_lock(s.vault.name)

    def _event(self, vault: str, what: str) -> None:
        self.events.append((self.clock(), vault, what))
        del self.events[:-500]

    def _after_lock(self, vault: str) -> None:
        for fn in self.on_lock:
            threading.Thread(target=fn, args=(vault,), name="after-lock", daemon=True).start()

    def locked_out(self, vault: str) -> float:
        """Seconds left of a lockout after too many wrong passwords (0 when not locked out)."""
        now = self.clock()
        recent = [t for t in self.failures.get(vault, []) if now - t < FAIL_WINDOW]
        self.failures[vault] = recent
        if len(recent) >= FAIL_LIMIT:
            return max(0.0, recent[-1] + FAIL_WINDOW - now)
        return 0.0

    # ------------------------------------------------------------ the flow

    def request_unlock(self, vault: str, app: str = "AI app", purpose: str = "", person: bool = False,
                       signin: bool = False) -> str:
        """A one-time code for the unlock page. Carries no secret; works once, for 5 minutes."""
        v = self.spec(vault, person)
        with self.lock_:
            now = self.clock()
            self.requests = {c: r for c, r in self.requests.items() if now - r.created < UNLOCK_LINK_TTL and not r.used}
            code = secrets.token_urlsafe(24)
            self.requests[code] = Request(v.name, app[:80], purpose[:300], now, signin=signin, person=person or signin)
            self._event(v.name, f"unlock asked by {app[:80]}" + (f": {purpose[:300]}" if purpose else ""))
            return code

    def describe(self, code: str) -> Request | None:
        r = self.requests.get(code)
        if r is None or r.used or self.clock() - r.created >= UNLOCK_LINK_TTL:
            return None
        return r

    def unlock(self, code: str, password: str, keep: str = "lock", read_only: bool = False) -> Session:
        with self.lock_:
            r = self.describe(code)
            if r is None:
                raise UnlockRefused("This unlock link has expired or was already used. Ask the AI to unlock again.")
            v = self.spec(r.vault, person=True)
            wait = self.locked_out(v.name)
            if wait:
                raise UnlockRefused(f"Too many wrong passwords. Try again in {math.ceil(wait / 60)} minutes.")
            if keep not in KEEP_CHOICES:
                raise UnlockRefused("Choose how long the vault stays open.")
            try:
                key = keys.unlock_masterkey((v.path / "masterkey.cryptomator").read_bytes(), password)
            except keys.WrongPassword:
                self.failures.setdefault(v.name, []).append(self.clock())
                self._event(v.name, "wrong password")
                left = FAIL_LIMIT - len(self.failures[v.name])
                raise UnlockRefused("Wrong password." + (f" {left} {'try' if left == 1 else 'tries'} left." if 0 < left <= 2 else ""))
            except FileNotFoundError:
                raise UnlockRefused("This vault's key file is missing. Check the vault's folder.")
            try:
                config = keys.verify_vault_config((v.path / "vault.cryptomator").read_bytes(), key)
            except Exception:
                key.wipe()
                raise
            r.used = True
            self.failures.pop(v.name, None)
            now = self.clock()
            seconds = KEEP_CHOICES[keep]
            expires = now + min(seconds or self.max_age, self.max_age)
            old = self.sessions.pop(v.name.casefold(), None)
            if old:
                old.key.wipe()
            s = Session(v, key, tree.Tree(v.path, key, config), read_only or v.mode == "read", keep, now, expires,
                        now, r.app, r.purpose)
            self.sessions[v.name.casefold()] = s
            self._event(v.name, f"unlocked for {r.app}, keep {keep}" + (", read only" if s.read_only else ""))
            return s

    def use(self, vault: str, person: bool = False) -> Session:
        """The open session for a vault, counting this as activity. Raises Locked if it isn't open."""
        v = self.spec(vault, person)
        with self.lock_:
            self.sweep()
            s = self.sessions.get(v.name.casefold())
            if s is None:
                raise Locked(f"The vault {v.name!r} is locked. Call unlock to ask the user to open it.")
            s.last_used = self.clock()
            return s

    def status(self, vault: str, person: bool = False) -> Session | None:
        with self.lock_:
            self.sweep()
            return self.sessions.get(self.spec(vault, person).name.casefold())

    def by_status_code(self, code: str) -> Session | None:
        with self.lock_:
            self.sweep()
            return next((s for s in self.sessions.values() if secrets.compare_digest(s.status_code, code)), None)

    def lock(self, vault: str, reason: str = "locked") -> bool:
        with self.lock_:
            s = self.sessions.pop(self.spec(vault, person=True).name.casefold(), None)
            if s is None:
                return False
            s.key.wipe()
            self._event(s.vault.name, reason)
            self._after_lock(s.vault.name)
            return True

    def lock_all(self, reason: str = "locked") -> None:
        with self.lock_:
            for name in list(self.sessions):
                s = self.sessions.pop(name)
                s.key.wipe()
                self._event(s.vault.name, reason)
                self._after_lock(s.vault.name)

    def sweep(self) -> None:
        """Locks what has been idle too long or reached its time."""
        with self.lock_:
            now = self.clock()
            for name, s in list(self.sessions.items()):
                if now >= s.expires:
                    self.lock(s.vault.name, "locked: time is up")
                elif now - s.last_used >= self.idle_for(s.vault):
                    self.lock(s.vault.name, f"locked: no use for {int(self.idle_for(s.vault) // 60)} minutes")

    def seconds_left(self, s: Session) -> int:
        """Until the vault locks by itself: the sooner of the idle limit and the time chosen."""
        now = self.clock()
        return max(0, int(min(s.expires - now, s.last_used + self.idle_for(s.vault) - now)))

    def idle_for(self, v: VaultSpec) -> float:
        """Seconds without use before this vault locks: its own setting, or the one for all vaults."""
        return v.idle_minutes * 60 if v.idle_minutes else self.idle

    def start_sweeper(self, every: float = 15.0) -> threading.Thread:
        def loop():
            while True:
                time.sleep(every)
                self.sweep()
        t = threading.Thread(target=loop, name="auto-lock", daemon=True)
        t.start()
        return t
