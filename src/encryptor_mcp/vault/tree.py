# SPDX-License-Identifier: AGPL-3.0-only
"""Reading a vault's folder tree: clear paths in, encrypted files out.

Inside a folder's directory d/XX/YYYY..., each entry is:
- name.c9r (a file): a regular file holding the encrypted contents;
- name.c9r/ with dir.c9r inside: a folder; dir.c9r holds the child folder's ID as plain ASCII;
- name.c9r/ with symlink.c9r inside: a link; symlink.c9r holds the target, encrypted like file contents;
- name.c9s/ (a shortened long name): name.c9s holds the full encrypted name, and one of contents.c9r (file),
  dir.c9r (folder) or symlink.c9r (link).
dirid.c9r (the folder's own ID, as a backup) and anything starting with "." or not ending in .c9r/.c9s are skipped.
Conflict copies (like "ABC (1).c9r") are reported, not read, until conflict handling is built.
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .content import Content
from .keys import Masterkey, VaultConfig, VaultError
from .names import C9R, C9S, MAX_DIR_ID_LENGTH, ROOT_DIR_ID, Names

MAX_NAME_FILE = 4096       # name.c9s holds one encrypted name; refuse anything bigger
MAX_SYMLINK = 32767 + 4096


@dataclass
class Entry:
    name: str           # the clear name
    kind: str           # "file", "dir" or "link"
    stored: Path        # where it is on disk (the .c9r file, or the .c9r/.c9s folder)
    dir_id: bytes | None = None
    parent_id: bytes | None = None   # the ID of the folder it's in (None for the root)


class NotFound(VaultError):
    pass


class Tree:
    def __init__(self, root: Path, key: Masterkey, config: VaultConfig):
        self.root = Path(root)
        self.names = Names(key, config.shortening_threshold)
        self.content = Content(key, config.cipher_combo)
        self.cipher_combo = config.cipher_combo
        self.vault_id = config.vault_id
        self.conflicts: list[Path] = []

    def dir_location(self, dir_id: bytes) -> Path:
        xx, rest = self.names.dir_path(dir_id)
        return self.root / "d" / xx / rest

    def _entry(self, path: Path, dir_id: bytes) -> Entry | None:
        e = self._entry_inner(path, dir_id)
        if e:
            e.parent_id = dir_id
        return e

    def _entry_inner(self, path: Path, dir_id: bytes) -> Entry | None:
        name = path.name
        if name.startswith(".") or name == "dirid.c9r":
            return None
        if name.endswith(C9S) and path.is_dir():
            name_file = path / "name.c9s"
            if not name_file.is_file() or name_file.stat().st_size > MAX_NAME_FILE:
                raise VaultError(f"A shortened name's name.c9s is missing or too large: {path.name}")
            full = name_file.read_text("ascii").strip()
            clear = self.names.decrypt(full, dir_id)
            if (path / "dir.c9r").is_file():
                return Entry(clear, "dir", path, self._read_dir_id(path / "dir.c9r"))
            if (path / "symlink.c9r").is_file():
                return Entry(clear, "link", path)
            if (path / "contents.c9r").is_file():
                return Entry(clear, "file", path)
            raise VaultError(f"A shortened entry has no contents: {path.name}")
        if not name.endswith(C9R):
            return None
        try:
            clear = self.names.decrypt(name, dir_id)
        except VaultError:
            self.conflicts.append(path)   # most often a sync conflict copy like "ABC (1).c9r"
            return None
        if path.is_dir():
            if (path / "dir.c9r").is_file():
                return Entry(clear, "dir", path, self._read_dir_id(path / "dir.c9r"))
            if (path / "symlink.c9r").is_file():
                return Entry(clear, "link", path)
            raise VaultError(f"An entry folder has neither dir.c9r nor symlink.c9r: {path.name}")
        return Entry(clear, "file", path)

    @staticmethod
    def _read_dir_id(path: Path) -> bytes:
        data = path.read_bytes()
        if not data or len(data) > MAX_DIR_ID_LENGTH:
            raise VaultError(f"A folder ID file is empty or too long: {path.parent.name}")
        return data

    def list_dir(self, dir_id: bytes = ROOT_DIR_ID) -> list[Entry]:
        location = self.dir_location(dir_id)
        if not location.is_dir():
            raise VaultError("A folder's encrypted directory is missing (the vault may be incomplete or still syncing).")
        out = []
        for path in sorted(location.iterdir()):
            entry = self._entry(path, dir_id)
            if entry:
                out.append(entry)
        return sorted(out, key=lambda e: e.name)

    def resolve(self, clear_path: str) -> Entry:
        """The entry at a clear path like 'Folder A/notes.txt' ('' or '/' is the root folder)."""
        parts = [unicodedata.normalize("NFC", p) for p in clear_path.strip("/").split("/") if p]
        entry = Entry("", "dir", self.dir_location(ROOT_DIR_ID), ROOT_DIR_ID)
        for i, part in enumerate(parts):
            if part in (".", ".."):
                raise VaultError("Paths can't contain '.' or '..'.")
            if entry.kind != "dir":
                raise NotFound(f"'{'/'.join(parts[:i])}' isn't a folder.")
            match = next((e for e in self.list_dir(entry.dir_id) if e.name == part), None)
            if match is None:
                raise NotFound(f"No '{'/'.join(parts[:i + 1])}' in this vault.")
            entry = match
        return entry

    def read_file(self, entry: Entry) -> bytes:
        if entry.kind != "file":
            raise VaultError(f"'{entry.name}' isn't a file.")
        path = entry.stored / "contents.c9r" if entry.stored.is_dir() else entry.stored
        return self.content.decrypt(path.read_bytes())

    @staticmethod
    def contents_path(entry: Entry) -> Path:
        """The encrypted contents file of a file entry (inside the .c9s folder for long names)."""
        return entry.stored / "contents.c9r" if entry.stored.is_dir() else entry.stored

    def file_size(self, entry: Entry) -> int:
        path = self.contents_path(entry)
        return self.content.cleartext_size(path.stat().st_size)

    def read_link(self, entry: Entry) -> str:
        data = (entry.stored / "symlink.c9r").read_bytes()
        if len(data) > MAX_SYMLINK:
            raise VaultError("A link's target is too long.")
        return self.content.decrypt(data).decode("utf-8")

    def locate(self, clear_path: str) -> dict:
        """Where a clear path lives on disk: its encrypted entry, and for a folder its contents folder too."""
        e = self.resolve(clear_path)
        out = {"entry": e.stored.relative_to(self.root).as_posix(), "kind": e.kind}
        if e.kind == "file":
            out["contents"] = self.contents_path(e).relative_to(self.root).as_posix()
        if e.kind == "dir":
            out["folder"] = self.dir_location(e.dir_id).relative_to(self.root).as_posix()
        return out

    def decrypt_path(self, encrypted: str) -> str:
        """The clear path for an encrypted path inside the vault, like d/AB/CDEF.../name.c9r (or .../name.c9s/...,
        or a contents folder d/AB/CDEF...). Raises NotFound when it belongs to no folder of this vault."""
        rel = encrypted.strip().replace("\\", "/").strip("/")
        parts = rel.split("/")
        if len(parts) < 3 or parts[0] != "d":
            raise VaultError("Give a path inside the vault that starts with d/, like d/AB/CDEF.../name.c9r.")
        folders = {self.dir_location(ROOT_DIR_ID): ("", ROOT_DIR_ID)}
        for path, e in self.walk():
            if e.kind == "dir":
                folders[self.dir_location(e.dir_id)] = (path, e.dir_id)
        loc = self.root / "d" / parts[1] / parts[2]
        if loc not in folders:
            raise NotFound("No folder of this vault is stored there (it may be an orphan: run the health check).")
        clear, dir_id = folders[loc]
        if len(parts) == 3:
            return clear or "/"
        name = parts[3]
        if name.endswith(C9S):
            name_file = loc / name / "name.c9s"
            if not name_file.is_file():
                raise NotFound("That long name's name.c9s is missing.")
            name = name_file.read_text("ascii").strip()
        return f"{clear}/{self.names.decrypt(name, dir_id)}"

    def walk(self, dir_id: bytes = ROOT_DIR_ID, prefix: str = ""):
        """Every entry below a folder, depth first: (clear path, entry)."""
        for entry in self.list_dir(dir_id):
            path = f"{prefix}/{entry.name}"
            yield path, entry
            if entry.kind == "dir":
                yield from self.walk(entry.dir_id, path)
