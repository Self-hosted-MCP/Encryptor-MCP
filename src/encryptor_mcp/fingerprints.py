# SPDX-License-Identifier: AGPL-3.0-only
"""The fingerprint list: catches what the vault format itself can't.

Cryptomator's format 8 can't notice a file cut exactly between two of its parts, nor two files whose encrypted
contents were swapped within a folder (contents aren't tied to their names). So Encryptor keeps, for every file, its
header's random code, its encrypted size, and its first part's random code, and compares later:
- same header, same first part, shorter, ending exactly between parts: it was cut (CutFile)
- two files that swapped their codes: their contents were swapped (SwappedFiles)
- anything else is a normal save elsewhere (Cryptomator keeps a file's header when it edits it, but writes its parts
  again; appending keeps the start): counted, never alarmed
The list is stored outside the vault (so whoever can change the vault's files can't change it) and encrypted with a
key made from the vault's own key (so only someone who can open the vault can read it). It's recorded the first time
a health check runs, and kept in step with every change made through Encryptor.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .changes import META
from .store import private_write_bytes
from .vault.health import Finding
from .vault.keys import Masterkey
from .vault.tree import Tree


class Fingerprints:
    def __init__(self, folder: Path, key: Masterkey, tree: Tree):
        self.tree = tree
        self.path = Path(folder) / f"{hashlib.sha256(tree.vault_id.encode()).hexdigest()[:24]}.bin"
        self._key = hmac.new(bytes(key.mac), b"encryptor-mcp fingerprint list v1", hashlib.sha256).digest()
        self.files: dict[str, list] = {}   # clear path -> [header code (hex), encrypted size]
        self.recorded = 0.0
        self.load()

    # ------------------------------------------------ storage
    def load(self) -> None:
        try:
            raw = self.path.read_bytes()
            data = json.loads(AESGCM(self._key).decrypt(raw[:12], raw[12:], b"fingerprints"))
            self.files, self.recorded = data["files"], data["recorded"]
        except FileNotFoundError:
            pass
        except (InvalidTag, ValueError, KeyError):
            self.files, self.recorded = {}, 0.0   # unreadable: start again rather than trust it

    def save(self) -> None:
        nonce = os.urandom(12)
        body = json.dumps({"files": self.files, "recorded": self.recorded}).encode()
        private_write_bytes(self.path, nonce + AESGCM(self._key).encrypt(nonce, body, b"fingerprints"))

    # ------------------------------------------------ reading the vault
    def _print(self, entry) -> list:
        p = self.tree.contents_path(entry)
        c = self.tree.content._c
        with open(p, "rb") as f:
            code = f.read(c.nonce_size).hex()
            f.seek(c.header_size)
            first = f.read(c.nonce_size).hex()   # the first part's own random code (same length as the header's)
        return [code, p.stat().st_size, first]

    def scan(self, start: str = "/") -> dict[str, list]:
        """Fingerprints of every file at or below a path, now (Encryptor's own records folder left out)."""
        out = {}
        try:
            e = self.tree.resolve(start)
        except Exception:
            return out
        if e.kind == "file":
            return {start: self._print(e)}
        if e.kind != "dir":
            return out
        prefix = "" if start == "/" else start.rstrip("/")
        for path, item in self.tree.walk(e.dir_id, prefix):
            if item.kind == "file" and not path.lstrip("/").casefold().startswith(META):
                try:
                    out[path] = self._print(item)
                except OSError:
                    pass
        return out

    def record_all(self) -> int:
        """Remember the whole vault as it is now."""
        self.files, self.recorded = self.scan("/"), time.time()
        self.save()
        return len(self.files)

    def after_change(self, rec: dict) -> None:
        """Keeps the list in step with a change made through Encryptor (a change record from changes.py)."""
        if not self.recorded:
            return
        touched = [p for p in (rec.get("path"), rec.get("to"), rec.get("source")) if p and p != "/"]
        for p in touched:
            base = p.rstrip("/")
            for k in [k for k in self.files if k == base or k.startswith(base + "/")]:
                del self.files[k]
            self.files.update(self.scan(base))
        self.save()

    # ------------------------------------------------ comparing
    def compare(self) -> list[Finding]:
        if not self.recorded:
            return []
        now = self.scan("/")
        out = []
        by_code = {v[0]: k for k, v in self.files.items()}
        changed = gone = new = 0
        c = self.tree.content
        for path, (code, size, first) in now.items():
            old = self.files.get(path)
            if old and old[0] == code:
                clean_cut = (size - c._c.header_size) % c.chunk_size == 0
                if len(old) > 2 and old[2] == first and size < old[1] and clean_cut:
                    out.append(Finding("CutFile", "warn", path,
                                       f"This file is shorter than when it was last seen ({old[1] - size} bytes gone "
                                       "from the end) while its start is unchanged: it looks cut, for example by an "
                                       "interrupted copy or sync. Check it, or restore an earlier version.", ""))
                elif old[1:] != [size, first][:len(old) - 1]:
                    changed += 1
                continue
            other = by_code.get(code)
            if other and other != path:
                theirs = now.get(other)
                if theirs and old and theirs[0] == old[0]:
                    if path < other:   # report each swapped pair once
                        out.append(Finding("SwappedFiles", "critical", path,
                                           f"This file and {other} have swapped contents.", ""))
                continue
            if old:
                changed += 1
            else:
                new += 1
        gone = sum(1 for p in self.files if p not in now)
        if changed or new or gone:
            parts = [f"{n} {w}" for n, w in ((changed, "saved again"), (new, "new"), (gone, "gone")) if n]
            out.append(Finding("ChangedElsewhere", "info", "/",
                               "Since the fingerprints were recorded, files were changed outside Encryptor (for example "
                               "on another device): " + ", ".join(parts) + ". That's normal.",
                               "Remember the vault as it is now."))
        return out
