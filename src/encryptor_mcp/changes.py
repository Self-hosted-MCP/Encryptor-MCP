# SPDX-License-Identifier: AGPL-3.0-only
"""Every change made through Encryptor-MCP is logged, keeps what it replaced, and can be undone.

Everything is stored inside the vault itself, encrypted like any other file, so it syncs with the vault and no
one without the password can read it:
    /.encryptor/changes/<id>.json   one record per change: when, which app, why, what, and how to undo it
    /.encryptor/versions/<id>       the contents a change replaced (copied encrypted, never decrypted)
    /.encryptor/trash/<id>          what was put in the trash (a file or a whole folder)
The AI can't read or change /.encryptor directly; it uses changes, versions, undo and the trash tools.

Safe writes: one writer at a time per vault (a lock in this program and a lock file on this computer), and
replacing a file needs the version seen when it was read, so a change made meanwhile (by you, another app or a
sync) is never overwritten blindly. Undo refuses too when the file changed since.
Deleting for good happens only by emptying the trash, which the person approves outside the chat.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sys
import threading
import time
import unicodedata
from contextlib import contextmanager
from pathlib import Path

from .vault.keys import VaultError
from .vault.tree import Entry, NotFound, Tree
from .vault.writer import Writer, parent_and_name

META = ".encryptor"
MAX_CHANGES_PER_MINUTE = 60
_locks: dict[str, threading.Lock] = {}
_last_us = 0


def _try_lock(f) -> bool:
    """An exclusive lock on an open file, without waiting: fcntl on macOS and Linux, msvcrt on Windows.
    Released when the file is closed."""
    try:
        if sys.platform == "win32":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


class Refused(VaultError):
    """A plain-words reason a change wasn't made."""


def clean(path: str) -> str:
    """A tidy absolute path, in NFC (names are stored NFC; macOS often sends decomposed names)."""
    parts = [unicodedata.normalize("NFC", p) for p in (path or "").strip("/").split("/") if p]
    if parts and parts[0].casefold() == META:
        raise Refused(f"'{META}' holds Encryptor's own records; use changes, versions, undo and the trash tools.")
    return "/" + "/".join(parts)


def is_meta(path: str) -> bool:
    parts = [p for p in (path or "").strip("/").split("/") if p]
    return bool(parts) and parts[0].casefold() == META


class Journal:
    def __init__(self, tree: Tree, lock_dir: Path | None = None, clock=time.time):
        self.t = tree
        self.w = Writer(tree)
        self.clock = clock
        key = hashlib.sha256(str(tree.root.resolve()).encode()).hexdigest()[:24]
        self.thread_lock = _locks.setdefault(key, threading.Lock())
        self.lock_file = (lock_dir / f"{key}.lock") if lock_dir else None
        self.recent: list[float] = []

    # ------------------------------------------------------------ plumbing

    @contextmanager
    def _locked(self):
        if not self.thread_lock.acquire(timeout=30):
            raise Refused("Another change to this vault is still running. Try again in a moment.")
        f = None
        try:
            if self.lock_file:
                self.lock_file.parent.mkdir(parents=True, exist_ok=True)
                f = open(self.lock_file, "a+")
                for _ in range(60):
                    if _try_lock(f):
                        break
                    time.sleep(0.5)
                else:
                    raise Refused("Another program is changing this vault. Try again in a moment.")
            yield
        finally:
            if f:
                f.close()
            self.thread_lock.release()

    def _brake(self) -> None:
        now = self.clock()
        self.recent = [t for t in self.recent if now - t < 60]
        if len(self.recent) >= MAX_CHANGES_PER_MINUTE:
            raise Refused(f"More than {MAX_CHANGES_PER_MINUTE} changes in a minute: slowing down. Try again shortly.")
        self.recent.append(now)

    def _meta(self, sub: str, create: bool = True) -> Entry | None:
        """/.encryptor/<sub>, made on the first change. Only looking (create=False) never writes anything."""
        root = self.t.resolve("/")
        top = next((e for e in self.t.list_dir(root.dir_id) if e.name == META), None)
        if top is None:
            if not create:
                return None
            top = self.w.make_dir(root, META)
        found = next((e for e in self.t.list_dir(top.dir_id) if e.name == sub), None)
        if found is None and create:
            found = self.w.make_dir(top, sub)
        return found

    def _new_id(self) -> str:
        """Sorts by time, strictly increasing within this program (microseconds, bumped if equal)."""
        global _last_us
        us = max(int(self.clock() * 1_000_000), _last_us + 1)
        _last_us = us
        s, micro = divmod(us, 1_000_000)
        return time.strftime("%Y%m%d-%H%M%S", time.gmtime(s)) + f".{micro:06d}-{secrets.token_hex(2)}"

    def _save(self, rec: dict) -> None:
        folder = self._meta("changes")
        name = f"{rec['id']}.json"
        data = json.dumps(rec, ensure_ascii=False, indent=1).encode()
        old = next((e for e in self.t.list_dir(folder.dir_id) if e.name == name), None)
        self.w.write_file(folder, name, data, replace=old)

    def _record(self, action: str, path: str, app: str, purpose: str, **extra) -> dict:
        rec = {"id": extra.pop("id", None) or self._new_id(), "time": int(self.clock()), "app": app[:80],
               "purpose": (purpose or "")[:300], "action": action, "path": path, **extra}
        self._save(rec)
        return rec

    def _keep_version(self, entry: Entry, change_id: str) -> str:
        self.w.copy_file(entry, self._meta("versions"), change_id)
        return change_id

    def etag(self, entry: Entry) -> str:
        """A short fingerprint of a file's encrypted contents: changes whenever the file changes."""
        return hashlib.sha256(self.t.contents_path(entry).read_bytes()).hexdigest()[:16]

    def _get(self, path: str) -> Entry:
        return self.t.resolve(path)

    def _exists(self, path: str) -> Entry | None:
        try:
            return self.t.resolve(path)
        except NotFound:
            return None

    # ------------------------------------------------------------ changes

    def write(self, path: str, data: bytes, version: str, app: str, purpose: str) -> dict:
        path = clean(path)
        with self._locked():
            self._brake()
            existing = self._exists(path)
            parent, name = parent_and_name(self.t, path)
            cid = self._new_id()
            if existing is None:
                e = self.w.write_file(parent, name, data)
                return self._record("create", path, app, purpose, id=cid, after=self.etag(e))
            if existing.kind != "file":
                raise Refused(f"'{path}' is a {'folder' if existing.kind == 'dir' else 'link'}, not a file.")
            if not version:
                raise Refused(f"'{path}' already exists. Read it first and pass its version to replace it, "
                              "or use append_file.")
            if version != self.etag(existing):
                raise Refused(f"'{path}' changed since you read it. Read it again before replacing it.")
            saved = self._keep_version(existing, cid)
            self.w.write_file(parent, name, data, replace=existing)
            return self._record("write", path, app, purpose, id=cid, saved=saved, after=self.etag(existing))

    def append(self, path: str, data: bytes, app: str, purpose: str) -> dict:
        path = clean(path)
        with self._locked():
            self._brake()
            existing = self._get(path)
            if existing.kind != "file":
                raise Refused(f"'{path}' isn't a file.")
            parent, name = parent_and_name(self.t, path)
            cid = self._new_id()
            old = self.t.read_file(existing)
            saved = self._keep_version(existing, cid)
            self.w.write_file(parent, name, old + data, replace=existing)
            return self._record("append", path, app, purpose, id=cid, saved=saved, after=self.etag(existing))

    def mkdir(self, path: str, app: str, purpose: str) -> dict:
        path = clean(path)
        with self._locked():
            self._brake()
            parent, name = parent_and_name(self.t, path)
            self.w.make_dir(parent, name)
            return self._record("mkdir", path, app, purpose)

    def move(self, path: str, to: str, app: str, purpose: str) -> dict:
        path, to = clean(path), clean(to)
        with self._locked():
            self._brake()
            entry = self._get(path)
            parent, name = parent_and_name(self.t, to)
            self.w.move(entry, parent, name)
            return self._record("move", path, app, purpose, to=to)

    def move_over(self, path: str, to: str, app: str, purpose: str) -> dict:
        """Move a file onto an existing file (how many apps save: write a temporary file, then rename it over the
        original). The original's contents are kept as a version, so this is an undoable replace."""
        path, to = clean(path), clean(to)
        with self._locked():
            self._brake()
            src, dst = self._get(path), self._get(to)
            if src.kind != "file" or dst.kind != "file":
                raise Refused("Only a file can replace a file.")
            cid = self._new_id()
            saved = self._keep_version(dst, cid)
            self.w.remove(dst)
            parent, name = parent_and_name(self.t, to)
            e = self.w.move(src, parent, name)
            return self._record("write", to, app, purpose, id=cid, saved=saved, source=path, after=self.etag(e))

    def copy(self, path: str, to: str, app: str, purpose: str) -> dict:
        path, to = clean(path), clean(to)
        with self._locked():
            self._brake()
            parent, name = parent_and_name(self.t, to)
            e = self.w.copy_file(self._get(path), parent, name)
            return self._record("copy", to, app, purpose, source=path, after=self.etag(e))

    def trash(self, path: str, app: str, purpose: str) -> dict:
        path = clean(path)
        if path == "/":
            raise Refused("The top folder can't go in the trash.")
        with self._locked():
            self._brake()
            entry = self._get(path)
            cid = self._new_id()
            self.w.move(entry, self._meta("trash"), cid)
            return self._record("trash", path, app, purpose, id=cid, trash=cid, kind=entry.kind)

    def restore_version(self, path: str, version_id: str, app: str, purpose: str) -> dict:
        path = clean(path)
        with self._locked():
            self._brake()
            return self._put_version(path, version_id, app, purpose, "restore")

    def _put_version(self, path: str, version_id: str, app: str, purpose: str, action: str, **extra) -> dict:
        versions = self._meta("versions")
        stored = next((e for e in self.t.list_dir(versions.dir_id) if e.name == version_id), None)
        if stored is None:
            raise Refused(f"No saved version {version_id!r}.")
        data = self.t.contents_path(stored).read_bytes()
        cid = self._new_id()
        current = self._exists(path)
        if current is None:
            parent, name = parent_and_name(self.t, path)
            current = self.w.write_file(parent, name, b"")
            saved = None
        else:
            if current.kind != "file":
                raise Refused(f"'{path}' isn't a file.")
            saved = self._keep_version(current, cid)
        self.w.put_ciphertext(current, data)
        return self._record(action, path, app, purpose, id=cid, saved=saved, version=version_id,
                            after=self.etag(current), **extra)

    # ------------------------------------------------------------ undo

    def undo(self, change_id: str, app: str, purpose: str) -> dict:
        with self._locked():
            self._brake()
            recs = self.records(500)
            rec = (next((r for r in recs if r["id"] == change_id), None) if change_id
                   else next((r for r in recs if r["action"] not in ("undo", "empty_trash") and not r.get("undone_by")), None))
            if rec is None:
                raise Refused("Nothing to undo." if not change_id else f"No change {change_id!r}.")
            if rec.get("undone_by"):
                raise Refused(f"That change was already undone ({rec['undone_by']}).")
            if rec["action"] in ("undo", "empty_trash"):
                raise Refused("That can't be undone." if rec["action"] == "empty_trash"
                              else "An undo can't be undone; make the change again instead.")
            a, path = rec["action"], rec["path"]

            def unchanged() -> Entry:
                e = self._exists(path)
                if e is None or e.kind != "file" or self.etag(e) != rec.get("after"):
                    raise Refused(f"'{path}' changed since then, so undoing would lose newer work. "
                                  "Use versions and restore_version instead.")
                return e

            if a in ("create", "copy"):
                e = unchanged()
                cid = self._new_id()
                self.w.move(e, self._meta("trash"), cid)
                out = self._record("undo", path, app, purpose, id=cid, undo_of=rec["id"], trash=cid, kind="file",
                                   did=f"put '{path}' in the trash")
            elif a in ("write", "append", "restore"):
                unchanged()
                if rec.get("saved"):
                    out = self._put_version(path, rec["saved"], app, purpose, "undo", undo_of=rec["id"],
                                            did=f"put back '{path}' as it was before")
                else:
                    cid = self._new_id()
                    self.w.move(self._get(path), self._meta("trash"), cid)
                    out = self._record("undo", path, app, purpose, id=cid, undo_of=rec["id"], trash=cid,
                                       kind="file", did=f"put '{path}' in the trash")
            elif a == "mkdir":
                e = self._get(path)
                if e.kind != "dir" or self.t.list_dir(e.dir_id):
                    raise Refused(f"'{path}' isn't an empty folder any more; move or trash it instead.")
                self.w.remove(e)
                out = self._record("undo", path, app, purpose, undo_of=rec["id"], did=f"removed the empty folder '{path}'")
            elif a == "move":
                e = self._get(rec["to"])
                parent, name = parent_and_name(self.t, path)
                self.w.move(e, parent, name)
                out = self._record("undo", path, app, purpose, undo_of=rec["id"], did=f"moved '{rec['to']}' back to '{path}'")
            elif a == "trash":
                trash = self._meta("trash")
                e = next((x for x in self.t.list_dir(trash.dir_id) if x.name == rec["trash"]), None)
                if e is None:
                    raise Refused("It's no longer in the trash (the trash was emptied).")
                parent, name = parent_and_name(self.t, path)
                self.w.move(e, parent, name)
                out = self._record("undo", path, app, purpose, undo_of=rec["id"], did=f"took '{path}' back out of the trash")
            else:
                raise Refused(f"Don't know how to undo {a!r}.")
            rec["undone_by"] = out["id"]
            self._save(rec)
            return out

    # ------------------------------------------------------------ looking back

    def records(self, limit: int = 50) -> list[dict]:
        """The newest changes first."""
        folder = self._meta("changes", create=False)
        if folder is None:
            return []
        entries = sorted((e for e in self.t.list_dir(folder.dir_id) if e.name.endswith(".json")),
                         key=lambda e: e.name, reverse=True)[:max(1, limit)]
        out = []
        for e in entries:
            try:
                out.append(json.loads(self.t.read_file(e)))
            except (VaultError, ValueError):
                continue
        return out

    def versions(self, path: str) -> list[dict]:
        """Saved earlier versions of a file, newest first: [{id, time, app, action}]."""
        path = clean(path)
        return [{"id": r["saved"], "time": r["time"], "app": r["app"], "action": r["action"]}
                for r in self.records(1000) if r.get("path") == path and r.get("saved")]

    def trash_items(self) -> list[dict]:
        trash = self._meta("trash", create=False)
        if trash is None:
            return []
        there = {e.name for e in self.t.list_dir(trash.dir_id)}
        return [r for r in self.records(1000) if r.get("trash") in there]

    def empty_trash(self, item: str, app: str, purpose: str) -> dict:
        """Delete for good: one trash item (its change id), or everything when item is empty. Not undoable."""
        with self._locked():
            trash = self._meta("trash")
            targets = [e for e in self.t.list_dir(trash.dir_id) if not item or e.name == item]
            if item and not targets:
                raise Refused(f"No {item!r} in the trash.")
            for e in targets:
                self.w.remove_tree(e)
            return self._record("empty_trash", "/", app, purpose, removed=[e.name for e in targets])
