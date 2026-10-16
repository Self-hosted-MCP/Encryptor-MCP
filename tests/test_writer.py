# SPDX-License-Identifier: AGPL-3.0-only
"""Changing a vault: every kind of change, judged by Cryptomator's own code in both modes."""
import hashlib

import pytest

from conftest import official, open_tree, password
from test_vault import ours
from encryptor_mcp.vault.keys import VaultError
from encryptor_mcp.vault.writer import Exists, Writer, parent_and_name

LONG = "a long name " + "z" * 150


def put(t, path, data):
    parent, name = parent_and_name(t, path)
    return Writer(t).write_file(parent, name, data)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def test_every_change_reads_the_same_in_cryptomator(vault):
    path, mode = vault
    t = open_tree(path, mode)
    w = Writer(t)
    root = t.resolve("/")
    new = w.make_dir(root, "New folder")
    deep = w.make_dir(new, LONG + " folder")                        # a shortened folder name
    put(t, f"/New folder/{LONG} folder/inside.md", b"# deep\n")
    put(t, f"/New folder/{LONG}.txt", b"long file name\n")          # a shortened file name
    put(t, "/New folder/big.bin", bytes(range(256)) * 400)          # several chunks
    put(t, "/New folder/empty", b"")
    w.write_file(root, "hello.txt", b"replaced\n", replace=t.resolve("/hello.txt"))
    w.copy_file(t.resolve("/big.bin"), new, "copy of big.bin")
    # moves across every name shape: short->short, short->long, long->short, long->long, folders and links
    w.move(t.resolve("/empty.txt"), new, "moved empty.txt")
    w.move(t.resolve("/New folder/moved empty.txt"), new, LONG + " moved")
    w.move(t.resolve(f"/New folder/{LONG} moved"), root, "back.txt")
    w.move(t.resolve(f"/New folder/{LONG}.txt"), new, LONG + " renamed.txt")
    w.move(t.resolve("/Folder A"), new, "Folder A moved")
    w.move(t.resolve("/link to hello"), new, LONG + " link")
    w.move(t.resolve(f"/{'Long folder name ' + 'y' * 140}"), root, "Short again")
    w.remove(t.resolve("/New folder/empty"))
    gone = w.make_dir(root, "to remove")
    w.remove(gone)

    mine = ours(open_tree(path, mode))
    assert mine == official("dump", str(path), password(mode))
    names = [line.split("\t")[1] for line in mine]
    assert "/New folder/Folder A moved/Sub folder/notes ü é 日本.txt" in names
    assert f"/New folder/{LONG} folder/inside.md" in names and "/to remove" not in names
    assert "/back.txt" in names and "/Short again/inside.txt" in names and "/empty.txt" not in names
    assert not any(p.name.startswith(".encryptor-") for p in path.rglob("*"))


def test_cryptomator_writes_into_folders_we_made(vault):
    path, mode = vault
    t = open_tree(path, mode)
    w = Writer(t)
    w.make_dir(w.make_dir(t.resolve("/"), "Ours"), LONG)
    official("write", str(path), password(mode), f"/Ours/{LONG}/from java.txt", "hi from Cryptomator")
    t = open_tree(path, mode)
    assert t.read_file(t.resolve(f"/Ours/{LONG}/from java.txt")) == b"hi from Cryptomator"
    assert ours(t) == official("dump", str(path), password(mode))


def test_refuses_unsafe_changes(vault):
    path, mode = vault
    t = open_tree(path, mode)
    w = Writer(t)
    root = t.resolve("/")
    with pytest.raises(Exists):
        put(t, "/hello.txt", b"x")
    with pytest.raises(VaultError, match="isn't empty"):
        w.remove(t.resolve("/Folder A"))
    with pytest.raises(VaultError, match="into itself"):
        w.move(t.resolve("/Folder A"), t.resolve("/Folder A/Sub folder"), "loop")
    with pytest.raises(VaultError, match="top folder"):
        w.remove(root)
    for bad in ("", "a/b", "..", "."):
        with pytest.raises(VaultError):
            w.write_file(root, bad, b"x")
    assert ours(open_tree(path, mode)) == official("dump", str(path), password(mode))
