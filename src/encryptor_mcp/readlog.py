# SPDX-License-Identifier: AGPL-3.0-only
"""The read log: which files were opened, when, by which app, and why. Private to the person (only the control
center shows it; no tool gives it to an AI app).

Each line is one entry, encrypted with a key made from the vault's own key (so only someone who can open the vault
can read it) and chained to the line before it: every entry carries the fingerprint of the previous line, which is
also bound into its encryption. Changing, removing or reordering a line breaks the chain from there on, and a small
separate "head" (the number of entries and the last fingerprint, also encrypted) catches lines cut from the end.
Kept outside the vault, owner-only. Deleting both files at once can't be caught here: it starts a new, empty log.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import time
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .store import private_write_bytes
from .vault.keys import Masterkey

GENESIS = "0" * 64


class ReadLog:
    def __init__(self, folder: Path, key: Masterkey, vault_id: str, clock=time.time):
        name = hashlib.sha256(vault_id.encode()).hexdigest()[:24]
        self.path = Path(folder) / f"{name}.log"
        self.head_path = Path(folder) / f"{name}.head"
        self._aead = AESGCM(hmac.new(bytes(key.mac), b"encryptor-mcp read log v1", hashlib.sha256).digest())
        self.clock = clock
        self.lock = threading.Lock()
        self.recent: dict[str, float] = {}   # (who, path) -> last time, to count Finder's repeated looks once

    # ------------------------------------------------ writing
    def _seal(self, obj: dict, aad: bytes) -> str:
        nonce = os.urandom(12)
        return (nonce + self._aead.encrypt(nonce, json.dumps(obj, ensure_ascii=False).encode(), aad)).hex()

    def _open(self, line: str, aad: bytes) -> dict:
        raw = bytes.fromhex(line)
        return json.loads(self._aead.decrypt(raw[:12], raw[12:], aad))

    def _head(self) -> tuple[int, str]:
        try:
            h = self._open(self.head_path.read_text().strip(), b"head")
            return int(h["count"]), str(h["last"])
        except FileNotFoundError:
            return 0, GENESIS
        except (InvalidTag, ValueError, KeyError):
            return -1, ""   # a changed head

    def add(self, who: str, path: str, how: str, purpose: str = "", once_per: float = 0) -> None:
        """One entry. once_per: skip it if the same app looked at the same path within that many seconds."""
        with self.lock:
            now = self.clock()
            key = f"{who}\x00{path}\x00{how}"
            if once_per and now - self.recent.get(key, -1e18) < once_per:
                return
            self.recent[key] = now
            count, last = self._head()
            if count < 0:   # the head was tampered with: keep logging, the check will say so
                count, last = self._tail()
            entry = {"n": count + 1, "time": int(now), "who": who[:80], "path": path[:500], "how": how,
                     "purpose": (purpose or "")[:300], "prev": last}
            line = self._seal(entry, last.encode())
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "a") as f:
                f.write(line + "\n")
            digest = hashlib.sha256(line.encode()).hexdigest()
            private_write_bytes(self.head_path, self._seal({"count": count + 1, "last": digest}, b"head").encode())

    def _tail(self) -> tuple[int, str]:
        lines = self._lines()
        return len(lines), (hashlib.sha256(lines[-1].encode()).hexdigest() if lines else GENESIS)

    def _lines(self) -> list[str]:
        try:
            return [l for l in self.path.read_text().splitlines() if l.strip()]
        except FileNotFoundError:
            return []

    # ------------------------------------------------ reading and checking
    def read(self, limit: int = 50) -> tuple[list[dict], str]:
        """(the newest entries first, the integrity verdict in plain words)."""
        entries, problem = [], ""
        prev = GENESIS
        for i, line in enumerate(self._lines(), 1):
            try:
                e = self._open(line, prev.encode())
                if e.get("n") != i or e.get("prev") != prev:
                    raise ValueError
            except (InvalidTag, ValueError, KeyError):
                problem = f"Entry {i} was changed, removed or moved: the log can't be trusted from there on."
                break
            entries.append(e)
            prev = hashlib.sha256(line.encode()).hexdigest()
        if not problem:
            count, last = self._head()
            if count < 0:
                problem = "The log's head file was changed."
            elif count > len(entries):
                problem = f"The last {count - len(entries)} entries were removed."
            elif count < len(entries) or (count and last != prev):
                problem = "The log doesn't match its head: entries were added or changed outside Encryptor."
        verdict = problem or (f"Intact: {len(entries)} entries, each checked against the one before."
                              if entries else "Nothing read yet.")
        return list(reversed(entries))[:limit], verdict
