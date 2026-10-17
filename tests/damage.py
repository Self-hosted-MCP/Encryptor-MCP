# SPDX-License-Identifier: AGPL-3.0-only
"""Breaks copies of a test vault in the ways real vaults break (sync accidents, half-finished copies, other apps),
for the health check tests. Each function takes an open Tree and changes the files directly."""
import os
import shutil
from pathlib import Path


def entry_of(t, clear_path):
    return t.resolve(clear_path)


def missing_dirid_backup(t):
    e = entry_of(t, "/Folder A")
    (t.dir_location(e.dir_id) / "dirid.c9r").unlink()


def missing_content_dir(t):
    e = entry_of(t, "/Folder A/Sub folder")
    shutil.rmtree(t.dir_location(e.dir_id))


def orphan_content_dir(t):
    e = entry_of(t, "/Folder A/Sub folder")
    shutil.rmtree(e.stored)                     # the folder's entry is gone, its contents are left behind


def empty_dir_file(t):
    e = entry_of(t, "/Folder A")
    (e.stored / "dir.c9r").write_bytes(b"")


def missing_long_name(t):
    e = next(x for x in t.list_dir(entry_of(t, "/Folder A").dir_id) if x.stored.name.endswith(".c9s"))
    (e.stored / "name.c9s").unlink()


def mismatched_long_name(t):
    """A .c9s folder renamed (e.g. by a sync app): its name.c9s no longer matches the folder's name."""
    e = next(x for x in t.list_dir(entry_of(t, "/Folder A").dir_id) if x.stored.name.endswith(".c9s"))
    os.rename(e.stored, e.stored.parent / ("A" * 27 + "=.c9s"))


def unknown_type(t):
    e = entry_of(t, "/link to hello")
    (e.stored / "symlink.c9r").unlink()          # an entry folder with nothing inside


def ambiguous_type(t):
    e = entry_of(t, "/Folder A")
    shutil.copy(e.stored / "dir.c9r", e.stored / "symlink.c9r")


ALL = [missing_dirid_backup, missing_content_dir, orphan_content_dir, empty_dir_file, missing_long_name,
       mismatched_long_name, unknown_type, ambiguous_type]
