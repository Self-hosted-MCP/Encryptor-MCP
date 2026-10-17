# SPDX-License-Identifier: AGPL-3.0-only
"""The health check: is the vault's structure whole? Read-only; repairs are separate and asked for.

It covers what Cryptomator's own health check covers, with the same names for the same problems (so the two can be
compared in the tests), plus a few of its own:
- folders: MissingDirIdBackup, MissingContentDir, OrphanContentDir, EmptyDirFile, ObeseDirFile, DirIdCollision
- long names: MissingLongName, ObeseNameFile, LongShortNamesMismatch, NotDecodableLongName
- entry types: UnknownType (nothing inside), AmbiguousType (two kinds at once)
- Encryptor's own: DamagedFile (a file header that doesn't open, or an impossible size: cut or changed),
  ConflictCopy (a sync app's "name (1)" copy), NotDecodableName, LeftoverTempFile (from an interrupted save)
Every finding says where (the clear path when it can be known), what it means in plain words, and whether a safe
repair exists. Nothing here changes the vault.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .keys import VaultError
from .names import C9R, C9S, MAX_DIR_ID_LENGTH, ROOT_DIR_ID
from .tree import MAX_NAME_FILE, Tree

CONFLICT = re.compile(r" \(\d+\)|conflict", re.IGNORECASE)
SEVERITY_ORDER = {"critical": 0, "warn": 1, "info": 2}


@dataclass
class Finding:
    kind: str
    severity: str            # critical (data may be unreachable), warn (something is off), info (harmless)
    where: str               # the clear path, or the encrypted path when the clear one can't be known
    detail: str              # plain words
    fix: str = ""            # what the repair does, or "" when there is none
    data: dict = field(default_factory=dict)   # what the repair needs (never shown)


def check(t: Tree, files: bool = True) -> list[Finding]:
    """Every problem found, most serious first. files=False skips opening each file's header (faster)."""
    out: list[Finding] = []
    seen_ids: dict[bytes, str] = {}
    visited: set[Path] = set()
    queue: list[tuple[bytes, str]] = [(ROOT_DIR_ID, "/")]
    seen_ids[ROOT_DIR_ID] = "/"
    while queue:
        dir_id, clear = queue.pop()
        loc = t.dir_location(dir_id)
        visited.add(loc)
        if not loc.is_dir():
            out.append(Finding("MissingContentDir", "warn", clear,
                               "This folder's contents are missing (deleted, or not synced yet). It shows as empty.",
                               "Recreate it as an empty folder, so it opens again.", {"dir_id": dir_id}))
            continue
        backup = loc / "dirid.c9r"
        if dir_id != ROOT_DIR_ID or backup.exists():
            if not backup.exists():
                out.append(Finding("MissingDirIdBackup", "info", clear,
                                   "The backup of this folder's ID is missing. Everything works; the backup only "
                                   "helps recover the folder if its entry is ever lost.",
                                   "Write the backup again.", {"dir_id": dir_id}))
        for p in sorted(loc.iterdir()):
            _entry(t, p, dir_id, clear, out, seen_ids, queue, files)
    # content folders no entry points at
    d = t.root / "d"
    if d.is_dir():
        for two in sorted(d.iterdir()):
            if not two.is_dir():
                continue
            for loc in sorted(two.iterdir()):
                if loc.is_dir() and loc not in visited:
                    own = _backup_id(t, loc)
                    rel = loc.relative_to(t.root).as_posix()
                    out.append(Finding("OrphanContentDir", "warn", rel,
                                       "Files from a folder whose entry is missing (for example after a sync "
                                       "conflict). They can't be reached by name.",
                                       "Bring them back as a folder called 'Recovered' at the top." if own is not None
                                       else "", {"loc": str(loc), "dir_id": own}))
    return sorted(out, key=lambda f: (SEVERITY_ORDER[f.severity], f.where))


def _backup_id(t: Tree, loc: Path) -> bytes | None:
    """The folder ID kept in a content folder's dirid.c9r, if it's there and checks out."""
    try:
        own = t.content.decrypt((loc / "dirid.c9r").read_bytes())
    except (OSError, VaultError):
        return None
    return own if 0 < len(own) <= MAX_DIR_ID_LENGTH and t.dir_location(own) == loc else None


def _entry(t: Tree, p: Path, dir_id: bytes, clear: str, out: list, seen_ids: dict, queue: list, files: bool) -> None:
    name = p.name
    rel = p.relative_to(t.root).as_posix()
    if name.startswith(".encryptor-") and name.endswith(".tmp"):
        out.append(Finding("LeftoverTempFile", "info", rel, "A temporary file left by an interrupted save.",
                           "Delete it.", {"path": str(p)}))
        return
    if name.startswith(".") or name == "dirid.c9r":
        return
    full = None
    if name.endswith(C9S) and p.is_dir():
        name_file = p / "name.c9s"
        if not name_file.is_file():
            out.append(Finding("MissingLongName", "critical", rel,
                               "An entry with a long name lost the file that holds its name, so it can't be shown.", ""))
        elif name_file.stat().st_size > MAX_NAME_FILE:
            out.append(Finding("ObeseNameFile", "critical", rel, "The file holding a long name is far too big.", ""))
        else:
            full = name_file.read_text("ascii", errors="replace").strip()
            expected = base64.urlsafe_b64encode(hashlib.sha1(full.encode("ascii", "replace")).digest()).decode() + C9S
            if expected != name:
                out.append(Finding("LongShortNamesMismatch", "warn", rel,
                                   "A long-named entry's folder name doesn't match its stored name (often a renamed "
                                   "sync copy).", "Give the folder the name it should have.",
                                   {"path": str(p), "to": str(p.parent / expected)}))
    elif not name.endswith(C9R):
        return
    else:
        full = name
    shown = None
    if full is not None:
        try:
            shown = t.names.decrypt(full, dir_id)
        except VaultError:
            if CONFLICT.search(name):
                out.append(Finding("ConflictCopy", "warn", rel,
                                   "A copy made by a sync app during a conflict. Its name can't be read here; "
                                   "Cryptomator's desktop app can sort it out.", ""))
                return
            out.append(Finding("NotDecodableLongName" if name.endswith(C9S) else "NotDecodableName", "warn", rel,
                               "This name doesn't decrypt with this vault's keys (from another vault, or damaged).", ""))
    where = (clear.rstrip("/") + "/" + shown) if shown else rel
    if p.is_dir():
        kinds = [k for k in ("dir.c9r", "symlink.c9r", "contents.c9r") if (p / k).is_file()]
        if name.endswith(C9R):
            kinds = [k for k in kinds if k != "contents.c9r"]
        if not kinds:
            out.append(Finding("UnknownType", "critical", where,
                               "An entry with nothing inside: it isn't a file, a folder or a link any more.", ""))
            return
        if len(kinds) > 1:
            out.append(Finding("AmbiguousType", "critical", where,
                               "An entry that is two things at once (" + " and ".join(kinds) + ").", ""))
            return
        kind = kinds[0]
        if kind == "dir.c9r":
            data = (p / "dir.c9r").read_bytes()
            if not data:
                out.append(Finding("EmptyDirFile", "critical", where, "A folder entry lost its folder ID.", ""))
                return
            if len(data) > MAX_DIR_ID_LENGTH:
                out.append(Finding("ObeseDirFile", "critical", where, "A folder entry's ID file is far too big.", ""))
                return
            if data in seen_ids:
                out.append(Finding("DirIdCollision", "critical", where,
                                   f"Two folders share one ID (also {seen_ids[data]}): they show the same contents.", ""))
                return
            seen_ids[data] = where
            queue.append((data, where))
        elif kind == "contents.c9r" and files:
            _file(t, p / "contents.c9r", where, out)
        return
    if files:
        _file(t, p, where, out)


def _file(t: Tree, path: Path, where: str, out: list) -> None:
    try:
        t.content.check_ends(path)
    except (OSError, VaultError) as exc:
        out.append(Finding("DamagedFile", "critical", where,
                           f"This file can't be opened: {exc}", ""))


# ---------------------------------------------------------------- repairs

FIXABLE = {"MissingDirIdBackup", "MissingContentDir", "OrphanContentDir", "LongShortNamesMismatch", "LeftoverTempFile"}


def repair(t: Tree, f: Finding) -> str:
    """Applies the safe repair for one finding; returns what was done. Raises VaultError when there is none."""
    from .writer import Writer, _write_atomic
    if f.kind == "MissingDirIdBackup":
        _write_atomic(t.dir_location(f.data["dir_id"]) / "dirid.c9r", t.content.encrypt(f.data["dir_id"]))
        return f"Wrote the folder ID backup for {f.where}."
    if f.kind == "MissingContentDir":
        loc = t.dir_location(f.data["dir_id"])
        loc.mkdir(parents=True, exist_ok=True)
        _write_atomic(loc / "dirid.c9r", t.content.encrypt(f.data["dir_id"]))
        return f"{f.where} opens again, empty."
    if f.kind == "LeftoverTempFile":
        Path(f.data["path"]).unlink(missing_ok=True)
        return "Deleted the leftover temporary file."
    if f.kind == "LongShortNamesMismatch":
        src, dst = Path(f.data["path"]), Path(f.data["to"])
        if dst.exists():
            raise VaultError("The right name is already taken by another entry; nothing was changed.")
        os.rename(src, dst)
        return "Gave the entry its right folder name."
    if f.kind == "OrphanContentDir" and f.data.get("dir_id"):
        root = t.resolve("/")
        names = {e.name for e in t.list_dir(ROOT_DIR_ID)}
        name = next(n for n in (["Recovered"] + [f"Recovered {i}" for i in range(2, 1000)]) if n not in names)
        w = Writer(t)
        stored, full, short = w._slot(root.dir_id, name)
        stored.mkdir()
        if short:
            _write_atomic(stored / "name.c9s", full.encode("ascii"))
        _write_atomic(stored / "dir.c9r", f.data["dir_id"])
        return f"The lost files are back, in the folder /{name}."
    raise VaultError("There's no safe automatic repair for this one.")
