# SPDX-License-Identifier: AGPL-3.0-only
"""The fingerprint list catches what the format can't: files cut between parts, and swapped files."""
import os

import pytest

from conftest import official, open_tree, password
from encryptor_mcp.changes import Journal
from encryptor_mcp.fingerprints import Fingerprints
from encryptor_mcp.vault import keys
from encryptor_mcp.vault import health


def setup_fp(path, mode, tmp_path):
    key = keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), password(mode))
    t = open_tree(path, mode)
    return Fingerprints(tmp_path / "fp", key, t), t


def test_cut_between_parts_is_caught_only_by_fingerprints(vault, tmp_path):
    path, mode = vault
    fp, t = setup_fp(path, mode, tmp_path)
    assert fp.record_all() == 6
    big = t.contents_path(t.resolve("/big.bin"))
    cut = t.content._c.header_size + 2 * t.content.chunk_size          # keep 2 of the 4 parts: a clean cut
    big.write_bytes(big.read_bytes()[:cut])
    assert health.check(t) == []                                        # the format alone sees nothing wrong
    assert len(t.read_file(t.resolve("/big.bin"))) == 65536              # and it reads "fine", just shorter
    found = fp.compare()
    assert [(f.kind, f.where) for f in found] == [("CutFile", "/big.bin")]
    assert official("dump", str(path), password(mode))                  # Cryptomator doesn't notice either


def test_swapped_files_are_caught(vault, tmp_path):
    path, mode = vault
    fp, t = setup_fp(path, mode, tmp_path)
    fp.record_all()
    a, b = t.contents_path(t.resolve("/hello.txt")), t.contents_path(t.resolve("/empty.txt"))
    da, db = a.read_bytes(), b.read_bytes()
    a.write_bytes(db)
    b.write_bytes(da)
    assert health.check(t) == []                                        # each still decrypts fine
    assert t.read_file(t.resolve("/hello.txt")) == b""                  # ...but under the wrong name
    found = fp.compare()
    assert [f.kind for f in found] == ["SwappedFiles"] and "/empty.txt" in found[0].where + found[0].detail


def test_normal_edits_elsewhere_are_quiet(vault, tmp_path):
    path, mode = vault
    fp, t = setup_fp(path, mode, tmp_path)
    fp.record_all()
    official("write", str(path), password(mode), "/hello.txt", "edited in Cryptomator")
    found = fp.compare()
    assert [(f.kind, f.severity) for f in found] == [("ChangedElsewhere", "info")] and "1 saved again" in found[0].detail
    fp.record_all()
    assert fp.compare() == []


def test_changes_through_encryptor_keep_the_list_in_step(vault, tmp_path):
    path, mode = vault
    fp, t = setup_fp(path, mode, tmp_path)
    fp.record_all()
    j = Journal(t)
    j.after_change.append(fp.after_change)
    j.write("/new.txt", b"x", "", "t", "")
    j.move("/Folder A", "/Moved A", "t", "")
    j.write("/hello.txt", b"replaced", j.etag(t.resolve("/hello.txt")), "t", "")
    j.trash("/big.bin", "t", "")
    assert fp.compare() == []
    assert "/Moved A/Sub folder/notes ü é 日本.txt" in fp.files and "/big.bin" not in fp.files


def test_list_is_encrypted_and_tamper_proof(vault, tmp_path):
    path, mode = vault
    fp, t = setup_fp(path, mode, tmp_path)
    fp.record_all()
    raw = fp.path.read_bytes()
    assert b"hello" not in raw and b"big.bin" not in raw
    assert os.name == "nt" or oct(fp.path.stat().st_mode)[-3:] == "600"   # Windows has no such modes
    fp.path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    again, _ = setup_fp(path, mode, tmp_path)
    assert again.recorded == 0 and again.files == {}                    # a changed list is never trusted
