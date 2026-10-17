# SPDX-License-Identifier: AGPL-3.0-only
"""Logged changes, saved versions, the trash and undo; the vault stays readable by Cryptomator throughout."""
import threading

import pytest

from conftest import official, open_tree, password
from test_vault import ours
from encryptor_mcp.changes import Journal, Refused

A = ("Claude", "test")


@pytest.fixture
def j(vault, tmp_path):
    path, mode = vault
    return Journal(open_tree(path, mode), tmp_path / "locks"), path, mode


def text(j, p):
    return j.t.read_file(j.t.resolve(p))


def test_create_replace_and_undo(j):
    j, path, mode = j
    r = j.write("/notes.txt", b"one", "", *A)
    assert r["action"] == "create" and text(j, "/notes.txt") == b"one"
    with pytest.raises(Refused, match="Read it first"):
        j.write("/notes.txt", b"two", "", *A)
    with pytest.raises(Refused, match="changed since you read it"):
        j.write("/notes.txt", b"two", "0" * 16, *A)
    v = j.etag(j.t.resolve("/notes.txt"))
    j.write("/notes.txt", b"two", v, *A)
    j.append("/notes.txt", b" three", *A)
    assert text(j, "/notes.txt") == b"two three"
    assert [x["action"] for x in j.versions("/notes.txt")] == ["append", "write"]
    j.undo("", *A)
    assert text(j, "/notes.txt") == b"two"
    j.undo("", *A)
    assert text(j, "/notes.txt") == b"one"
    j.undo("", *A)                                         # the create: into the trash
    with pytest.raises(Exception):
        j.t.resolve("/notes.txt")
    assert len(j.trash_items()) == 1
    with pytest.raises(Refused, match="Nothing to undo"):
        j.undo("", *A)
    assert ours(open_tree(path, mode)) == official("dump", str(path), password(mode))


def test_undo_refuses_to_lose_newer_work(j):
    j, *_ = j
    j.write("/a.txt", b"v1", "", *A)
    first = j.write("/a.txt", b"v2", j.etag(j.t.resolve("/a.txt")), *A)
    j.write("/a.txt", b"v3", j.etag(j.t.resolve("/a.txt")), *A)
    with pytest.raises(Refused, match="changed since then"):
        j.undo(first["id"], *A)
    j.restore_version("/a.txt", first["saved"], *A)
    assert text(j, "/a.txt") == b"v1"


def test_trash_folders_and_take_back_out(j):
    j, path, mode = j
    before = ours(open_tree(path, mode))
    r = j.trash("/Folder A", *A)
    assert "/Folder A" not in [x.name for x in j.t.list_dir(b"")]
    j.undo(r["id"], *A)
    assert text(j, "/Folder A/Sub folder/notes ü é 日本.txt").startswith(b"Unicode")
    visible = [line for line in ours(open_tree(path, mode)) if "/.encryptor" not in line]
    assert visible == before
    with pytest.raises(Refused, match="already undone"):
        j.undo(r["id"], *A)


def test_move_copy_mkdir_undo(j):
    j, path, mode = j
    j.mkdir("/Box", *A)
    j.move("/hello.txt", "/Box/hi.txt", *A)
    j.copy("/Box/hi.txt", "/hello copy.txt", *A)
    assert text(j, "/hello copy.txt") == text(j, "/Box/hi.txt")
    j.undo("", *A)
    j.undo("", *A)
    assert text(j, "/hello.txt").startswith(b"Hello")
    j.undo("", *A)
    assert "Box" not in [x.name for x in j.t.list_dir(b"")]
    assert ours(open_tree(path, mode)) == official("dump", str(path), password(mode))


def test_empty_trash_is_for_good(j):
    j, path, mode = j
    r = j.trash("/Folder A", *A)
    j.trash("/big.bin", *A)
    j.empty_trash(r["trash"], *A)
    assert len(j.trash_items()) == 1
    with pytest.raises(Refused, match="trash was emptied"):
        j.undo(r["id"], *A)
    j.empty_trash("", *A)
    assert j.trash_items() == []
    with pytest.raises(Refused, match="can't be undone"):
        j.undo(j.records(1)[0]["id"], *A)
    assert ours(open_tree(path, mode)) == official("dump", str(path), password(mode))


def test_own_records_are_off_limits(j):
    j, *_ = j
    for bad in ("/.encryptor/changes/x.json", ".Encryptor/trash"):
        with pytest.raises(Refused, match="Encryptor's own records"):
            j.write(bad, b"x", "", *A)


def test_records_say_who_and_why(j):
    j, *_ = j
    j.write("/x.txt", b"x", "", "Cursor", "draft the letter")
    r = j.records(1)[0]
    assert (r["app"], r["purpose"], r["action"], r["path"]) == ("Cursor", "draft the letter", "create", "/x.txt")


def test_one_writer_at_a_time(j):
    j, *_ = j
    j.write("/count.txt", b"", "", *A)
    def add():
        for _ in range(5):
            j.append("/count.txt", b"x", *A)
    threads = [threading.Thread(target=add) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert text(j, "/count.txt") == b"x" * 20


def test_brake_on_too_many_changes(j):
    j, *_ = j
    j.recent = [j.clock()] * 60
    with pytest.raises(Refused, match="slowing down"):
        j.mkdir("/x", *A)


def test_new_names_without_control_characters(tmp_path):
    from encryptor_mcp.changes import Refused, clean
    for bad in ("/a\nb.txt", "/x/\r", "/tab\there", "/del\x7f"):
        with pytest.raises(Refused):
            clean(bad, new=True)
        assert clean(bad) == "/" + bad.strip("/")   # an existing odd name can still be found
