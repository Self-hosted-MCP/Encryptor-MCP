# SPDX-License-Identifier: AGPL-3.0-only
"""Changing a vault, exactly the way Cryptomator does, so its apps read every change.

- A file: its contents encrypted under a fresh file key, written to a temporary file next to the target, flushed
  to disk, then swapped in with one rename. A reader (or a sync app) sees the old file or the new one, never half.
- A folder: a new random folder ID; first its own encrypted directory d/XX/YYYY with dirid.c9r (the ID, encrypted,
  as a backup), then the entry name.c9r/ with dir.c9r (the ID in plain ASCII) in the parent.
- Long names (longer than the vault's limit once encrypted) go in a NAME.c9s folder with name.c9s holding the full
  encrypted name, beside contents.c9r, dir.c9r or symlink.c9r.
- Moving: names are bound to their folder, so the name is encrypted again for the new place and the stored entry
  renamed. File contents aren't tied to a path, so they move (and copy) without being decrypted.
Nothing here asks or logs; changes.py adds versions, the change log and undo on top.
"""

from __future__ import annotations

import os
import shutil
import time
import uuid
from pathlib import Path

from .keys import VaultError
from .names import C9S, ROOT_DIR_ID
from .tree import Entry, NotFound, Tree

TEMP_PREFIX = ".encryptor-"   # dot files are skipped by readers here and by Cryptomator


class Exists(VaultError):
    pass


def _write_atomic(path: Path, data: bytes) -> None:
    tmp = path.parent / f"{TEMP_PREFIX}{uuid.uuid4().hex}.tmp"
    try:
        with open(tmp, "xb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        for attempt in range(20):   # Windows refuses while another program (a sync app, an editor) has it open
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                if attempt == 19:
                    raise VaultError(f"'{path.name}' is in use by another program. Try again in a moment.")
                time.sleep(0.25)
    finally:
        if tmp.exists():
            tmp.unlink()


class Writer:
    def __init__(self, tree: Tree):
        self.tree = tree
        self.names = tree.names

    # ------------------------------------------------------------ where an entry goes

    def _slot(self, parent_id: bytes, name: str) -> tuple[Path, str, bool]:
        """(stored path, full encrypted name, shortened?) for a name in a folder."""
        full = self.names.encrypt(name, parent_id)
        stored, short = self.names.stored_name(full)
        return self.tree.dir_location(parent_id) / stored, full, short

    def _free(self, parent: Entry, name: str) -> tuple[Path, str, bool]:
        if parent.kind != "dir":
            raise VaultError(f"'{parent.name}' isn't a folder.")
        if any(e.name == name for e in self.tree.list_dir(parent.dir_id)):
            raise Exists(f"'{name}' already exists there.")
        return self._slot(parent.dir_id, name)

    # ------------------------------------------------------------ files

    def write_file(self, parent: Entry, name: str, data: bytes, replace: Entry | None = None) -> Entry:
        """A new file, or new contents for `replace` (an existing file in `parent`)."""
        if replace is not None:
            if replace.kind != "file":
                raise VaultError(f"'{replace.name}' isn't a file.")
            _write_atomic(self.tree.contents_path(replace), self.tree.content.encrypt(data))
            return replace
        stored, full, short = self._free(parent, name)
        ciphertext = self.tree.content.encrypt(data)
        if short:
            stored.mkdir()
            try:
                _write_atomic(stored / "name.c9s", full.encode("ascii"))
                _write_atomic(stored / "contents.c9r", ciphertext)
            except BaseException:
                shutil.rmtree(stored, ignore_errors=True)
                raise
        else:
            _write_atomic(stored, ciphertext)
        return Entry(name, "file", stored, None, parent.dir_id)

    def copy_file(self, entry: Entry, parent: Entry, name: str) -> Entry:
        """A copy of a file's encrypted contents under a new name (no decryption needed)."""
        if entry.kind != "file":
            raise VaultError(f"'{entry.name}' isn't a file. Only files can be copied.")
        stored, full, short = self._free(parent, name)
        data = self.tree.contents_path(entry).read_bytes()
        if short:
            stored.mkdir()
            _write_atomic(stored / "name.c9s", full.encode("ascii"))
            _write_atomic(stored / "contents.c9r", data)
        else:
            _write_atomic(stored, data)
        return Entry(name, "file", stored, None, parent.dir_id)

    # ------------------------------------------------------------ folders

    def make_dir(self, parent: Entry, name: str) -> Entry:
        stored, full, short = self._free(parent, name)
        dir_id = str(uuid.uuid4()).encode("ascii")
        location = self.tree.dir_location(dir_id)
        location.mkdir(parents=True)
        _write_atomic(location / "dirid.c9r", self.tree.content.encrypt(dir_id))
        stored.mkdir()
        if short:
            _write_atomic(stored / "name.c9s", full.encode("ascii"))
        _write_atomic(stored / "dir.c9r", dir_id)
        return Entry(name, "dir", stored, dir_id, parent.dir_id)

    def _is_inside(self, folder: Entry, maybe_parent_id: bytes) -> bool:
        """Whether the folder with ID maybe_parent_id is `folder` or somewhere below it."""
        if folder.dir_id == maybe_parent_id:
            return True
        return any(e.dir_id == maybe_parent_id for _, e in self.tree.walk(folder.dir_id) if e.kind == "dir")

    # ------------------------------------------------------------ moving and removing

    def move(self, entry: Entry, parent: Entry, name: str) -> Entry:
        """Move and/or rename an entry. Folders keep their ID, so everything inside stays where it is."""
        if entry.parent_id is None:
            raise VaultError("The top folder can't be moved.")
        if entry.kind == "dir" and self._is_inside(entry, parent.dir_id):
            raise VaultError("A folder can't be moved into itself.")
        stored, full, short = self._free(parent, name)
        src = entry.stored
        was_short = src.name.endswith(C9S) and src.is_dir()
        if entry.kind == "file":
            if was_short and short:
                os.rename(src, stored)
                _write_atomic(stored / "name.c9s", full.encode("ascii"))
            elif was_short:
                os.rename(src / "contents.c9r", stored)
                shutil.rmtree(src)
            elif short:
                stored.mkdir()
                _write_atomic(stored / "name.c9s", full.encode("ascii"))
                os.rename(src, stored / "contents.c9r")
            else:
                os.rename(src, stored)
        else:   # a folder or a link: the entry is a folder holding dir.c9r or symlink.c9r
            os.rename(src, stored)
            if short:
                _write_atomic(stored / "name.c9s", full.encode("ascii"))
            elif (stored / "name.c9s").exists():
                (stored / "name.c9s").unlink()
        return Entry(name, entry.kind, stored, entry.dir_id, parent.dir_id)

    def put_ciphertext(self, entry: Entry, data: bytes) -> None:
        """Put already-encrypted contents (an earlier version of a file) back in place, swapped in at once."""
        if entry.kind != "file":
            raise VaultError(f"'{entry.name}' isn't a file.")
        self.tree.content.cleartext_size(len(data))
        _write_atomic(self.tree.contents_path(entry), data)

    def remove_tree(self, entry: Entry) -> None:
        """Remove an entry and, for a folder, everything in it, deepest first. Only for emptying the trash."""
        if entry.kind == "dir":
            for child in self.tree.list_dir(entry.dir_id):
                self.remove_tree(child)
        self.remove(entry)

    def remove(self, entry: Entry) -> None:
        """Remove a file, a link, or an empty folder for good (changes.py moves to the trash instead)."""
        if entry.parent_id is None:
            raise VaultError("The top folder can't be removed.")
        if entry.kind == "dir":
            if self.tree.list_dir(entry.dir_id):
                raise VaultError(f"The folder '{entry.name}' isn't empty.")
            location = self.tree.dir_location(entry.dir_id)
            shutil.rmtree(location)
            try:
                location.parent.rmdir()   # d/XX, if nothing else is in it
            except OSError:
                pass
            shutil.rmtree(entry.stored)
        elif entry.stored.is_dir():
            shutil.rmtree(entry.stored)
        else:
            entry.stored.unlink()


def parent_and_name(tree: Tree, clear_path: str) -> tuple[Entry, str]:
    """The folder a path points into, and the last name: for creating or moving to a path."""
    parts = [p for p in clear_path.strip("/").split("/") if p]
    if not parts:
        raise VaultError("Give a path with a name, like 'Notes/today.txt'.")
    parent = tree.resolve("/".join(parts[:-1]))
    if parent.kind != "dir":
        raise NotFound(f"'{'/'.join(parts[:-1])}' isn't a folder.")
    return parent, parts[-1]


__all__ = ["Writer", "Exists", "parent_and_name", "ROOT_DIR_ID"]
