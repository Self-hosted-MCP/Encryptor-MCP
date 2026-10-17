# SPDX-License-Identifier: AGPL-3.0-only
"""Vault tools, judged by Cryptomator's own code: new vaults, passwords, recovery keys."""
import pytest

from conftest import FIXTURES, needs_cryptomator_app, official, open_tree, password
from encryptor_mcp.vault import health, keys, manage
from encryptor_mcp.vault.tree import Tree

NEW = "a brand new pass"


def tree_of(folder, pw):
    key = keys.unlock_masterkey((folder / "masterkey.cryptomator").read_bytes(), pw)
    return Tree(folder, key, keys.verify_vault_config((folder / "vault.cryptomator").read_bytes(), key))


def test_a_new_vault_opens_in_cryptomator(tmp_path):
    folder = tmp_path / "Fresh"
    manage.create_vault(folder, NEW).wipe()
    assert official("dump", str(folder), NEW) == []                        # empty, and Cryptomator opens it
    assert official("health", str(folder), NEW) == []                      # healthy by Cryptomator's own check
    official("write", str(folder), NEW, "/from cryptomator.txt", "hello")
    t = tree_of(folder, NEW)
    assert t.read_file(t.resolve("/from cryptomator.txt")) == b"hello" and health.check(t) == []
    with pytest.raises(keys.VaultError, match="isn't empty"):
        manage.create_vault(folder, NEW)
    with pytest.raises(keys.VaultError, match="at least 8"):
        manage.create_vault(tmp_path / "Other", "short")


def test_change_password(vault):
    path, mode = vault
    with pytest.raises(keys.WrongPassword):
        manage.change_password(path, "not the password", NEW)
    manage.change_password(path, password(mode), NEW)
    with pytest.raises(keys.WrongPassword):
        keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), password(mode))
    assert len(official("dump", str(path), NEW)) == 10                      # Cryptomator opens it with the new one
    assert not list(path.glob("masterkey.cryptomator*bkup*"))               # no copy left with the old password


def test_recovery_keys_match_cryptomator(vault):
    needs_cryptomator_app()
    path, mode = vault
    theirs = official("recoverykey", str(path), password(mode))[0].split("\t")[1]
    key = keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), password(mode))
    assert manage.recovery_key(key) == theirs and len(theirs.split()) == 44


def test_reset_with_cryptomators_key_and_the_other_way_round(vault):
    needs_cryptomator_app()
    path, mode = vault
    theirs = official("recoverykey", str(path), password(mode))[0].split("\t")[1]
    manage.reset_password(path, theirs, NEW)                                # ours, with Cryptomator's key
    assert len(official("dump", str(path), NEW)) == 10
    key = keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), NEW)
    official("resetpw", str(path), manage.recovery_key(key), "third password")   # Cryptomator's, with ours
    assert tree_of(path, "third password").resolve("/hello.txt")


def test_recovery_key_mistakes(vault):
    path, mode = vault
    key = keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), password(mode))
    words = manage.recovery_key(key).split()
    swapped = words[:]
    swapped[3], swapped[4] = swapped[4], swapped[3]
    with pytest.raises(keys.VaultError, match="doesn't check out"):
        manage.key_from_recovery(" ".join(swapped))
    with pytest.raises(keys.VaultError, match="44 words"):
        manage.key_from_recovery(" ".join(words[:40]))
    with pytest.raises(keys.VaultError, match="Not a recovery key word"):
        manage.key_from_recovery(" ".join(words[:43] + ["zzzzz"]))
    other = keys.unlock_masterkey((FIXTURES / "vault-SIV_CTRMAC" / "masterkey.cryptomator").read_bytes(),
                                  password("SIV_CTRMAC"))
    if mode == "SIV_GCM":
        with pytest.raises(keys.VaultError, match="different vault"):
            manage.reset_password(path, manage.recovery_key(other), NEW)
    assert keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), password(mode))   # untouched
    assert manage.key_from_recovery("  " + " ".join(w.upper() for w in words) + " ").raw == key.raw
