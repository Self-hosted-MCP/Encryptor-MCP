# SPDX-License-Identifier: AGPL-3.0-only
"""The vault format against Cryptomator's own code, in both cipher modes."""
import hashlib
import os

import pytest

from conftest import official, open_tree, password
from encryptor_mcp.vault import content, keys, names


def ours(t) -> list[str]:
    lines = []
    for path, e in t.walk():
        if e.kind == "dir":
            lines.append(f"dir\t{path}")
        elif e.kind == "link":
            lines.append(f"link\t{path}\t{t.read_link(e)}")
        else:
            data = t.read_file(e)
            assert len(data) == t.file_size(e)
            lines.append(f"file\t{path}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}")
    return sorted(lines)


def test_reads_exactly_like_cryptomator(vault):
    path, mode = vault
    assert ours(open_tree(path, mode)) == official("dump", str(path), password(mode))


def test_reads_known_contents(vault):
    path, mode = vault
    t = open_tree(path, mode)
    assert t.read_file(t.resolve("hello.txt")) == b"Hello from Cryptomator's own code.\n"
    assert t.read_file(t.resolve("/Folder A/Sub folder/notes ü é 日本.txt")).decode() == "Unicode name and text: ü é 日本\n"
    assert t.read_file(t.resolve("empty.txt")) == b""
    big = t.read_file(t.resolve("big.bin"))
    assert big == bytes((i * 31 + 7) & 0xFF for i in range(100_000))
    assert t.read_link(t.resolve("link to hello")) == "hello.txt"
    long_entry = next(e for e in t.list_dir(t.resolve("Folder A").dir_id) if e.name.startswith("a very long"))
    assert long_entry.stored.suffix == ".c9s"


def test_cryptomator_reads_what_we_write(vault):
    path, mode = vault
    t = open_tree(path, mode)
    folder = t.resolve("Folder A")
    files = {"written by encryptor ✓.txt": "Written by Encryptor-MCP.\n".encode(),
             "big.bin": os.urandom(70_000), "empty.txt": b""}
    for name, data in files.items():
        stored, _ = t.names.stored_name(t.names.encrypt(name, folder.dir_id))
        (t.dir_location(folder.dir_id) / stored).write_bytes(t.content.encrypt(data))
    seen = {line.split("\t")[1]: line for line in official("dump", str(path), password(mode))}
    for name, data in files.items():
        line = seen[f"/Folder A/{name}"]
        assert line.endswith(f"\t{len(data)}\t{hashlib.sha256(data).hexdigest()}")


def test_wrong_password(vault):
    path, _ = vault
    with pytest.raises(keys.WrongPassword):
        keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), "not the password")


def test_tampered_settings_file(vault):
    path, mode = vault
    key = keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), password(mode))
    data = bytearray((path / "vault.cryptomator").read_bytes())
    data[-3] = ord("A") if data[-3] != ord("A") else ord("B")
    with pytest.raises(keys.VaultError, match="signature"):
        keys.verify_vault_config(bytes(data), key)


@pytest.mark.parametrize("kid", ["masterkeyfile:/etc/passwd", "masterkeyfile:../other/masterkey.cryptomator", "file:x"])
def test_refuses_other_key_locations(vault, kid):
    import base64, json
    path, _ = vault
    head, claims, sig = (path / "vault.cryptomator").read_text().split(".")
    header = json.loads(base64.urlsafe_b64decode(head + "=" * (-len(head) % 4)))
    header["kid"] = kid
    new_head = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    with pytest.raises(keys.VaultError, match="key location"):
        keys.read_vault_config_unverified(f"{new_head}.{claims}.{sig}".encode())


def test_refuses_oversized_and_odd_key_files():
    with pytest.raises(keys.VaultError, match="too large"):
        keys.parse_masterkey_file(b"{" + b" " * 70_000 + b"}")
    with pytest.raises(keys.VaultError, match="scrypt"):
        keys.parse_masterkey_file(b'{"version":999,"scryptSalt":"AA==","scryptCostParam":3,"scryptBlockSize":8,'
                                  b'"primaryMasterKey":"","hmacMasterKey":"","versionMac":""}')


def test_changed_or_cut_files_are_refused(vault):
    path, mode = vault
    t = open_tree(path, mode)
    e = t.resolve("big.bin")
    data = bytearray(e.stored.read_bytes())
    data[200] ^= 1
    with pytest.raises(content.Corrupted):
        t.content.decrypt(bytes(data))
    with pytest.raises(content.Corrupted):
        t.content.decrypt(e.stored.read_bytes()[:-10])


def test_wiping_keys():
    k = keys.Masterkey(bytearray(os.urandom(32)), bytearray(os.urandom(32)))
    k.wipe()
    assert set(k.enc) == {0} and set(k.mac) == {0}


@pytest.mark.parametrize("mode", ["SIV_GCM", "SIV_CTRMAC"])
@pytest.mark.parametrize("size", [0, 1, 32767, 32768, 32769, 100_000])
def test_round_trip_sizes(mode, size):
    k = keys.Masterkey(bytearray(os.urandom(32)), bytearray(os.urandom(32)))
    c = content.Content(k, mode)
    blob = os.urandom(size)
    enc = c.encrypt(blob)
    assert c.decrypt(enc) == blob and c.cleartext_size(len(enc)) == size


def test_names_need_the_right_folder():
    k = keys.Masterkey(bytearray(os.urandom(32)), bytearray(os.urandom(32)))
    n = names.Names(k)
    enc = n.encrypt("Café.txt", b"folder-1")
    assert n.decrypt(enc, b"folder-1") == "Café.txt"
    assert n.encrypt("Café.txt", b"folder-1") == enc   # NFC: the same name either way
    with pytest.raises(keys.VaultError):
        n.decrypt(enc, b"folder-2")


def test_locate_and_decrypt_name_round_trip(vault):
    path, mode = vault
    t = open_tree(path, mode)
    for _, e in t.walk():
        pass
    checked = 0
    for clear, e in t.walk():
        where = t.locate(clear)
        assert t.decrypt_path(where["entry"]) == clear
        if e.kind == "dir":
            assert t.decrypt_path(where["folder"]) == clear
        checked += 1
    assert checked == 10
    assert t.decrypt_path(t.locate("/Folder A")["entry"] + "/") == "/Folder A"   # trailing slash is fine
    import pytest as _p
    with _p.raises(Exception, match="starts with d/"):
        t.decrypt_path("hello.txt")
    with _p.raises(Exception, match="No folder"):
        t.decrypt_path("d/ZZ/NOTAFOLDER/abc.c9r")
