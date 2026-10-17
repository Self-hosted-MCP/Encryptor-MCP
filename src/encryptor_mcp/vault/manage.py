# SPDX-License-Identifier: AGPL-3.0-only
"""Vault tools: create a vault, change its password, and the recovery key, all the way Cryptomator does them, so a
vault made here opens in Cryptomator, and a recovery key from either works in both.

- A new vault: format 8, SIV_GCM, long names shortened above 220 characters; a fresh 64-byte master key; the key file
  (masterkey.cryptomator, scrypt N=32768 r=8) and the signed settings file (vault.cryptomator); the root folder.
- The recovery key: the 64-byte master key plus the 2 low bytes of its CRC-32 (little-endian), written as 44 words from Cryptomator's own
  list of 4096 words (words_en.txt, from Cryptomator, GPL-3.0): every 3 bytes become 2 words of 12 bits each.
- Changing the password re-wraps the same master key with the new one (as in Cryptomator: the master key itself
  doesn't change). The key file is replaced at once; no copy wrapped with the old password is left behind.
- Resetting a forgotten password takes the recovery key, checks it against the vault's signed settings file, and
  writes a new key file.
Passwords are NFC-normalised (keys.normalize_password) and need at least 8 characters, like Cryptomator.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid
import zlib
from importlib.resources import files
from pathlib import Path

from .content import Content
from .keys import Masterkey, VaultError, read_vault_config_unverified, verify_vault_config, write_masterkey_file
from .names import ROOT_DIR_ID, Names

MIN_PASSWORD = 8
WORDS = files(__package__).joinpath("words_en.txt").read_text("utf-8").split()
INDEX = {w: i for i, w in enumerate(WORDS)}
assert len(WORDS) == 4096 and len(INDEX) == 4096


# ---------------------------------------------------------------- the recovery key

def recovery_key(key: Masterkey) -> str:
    raw = key.raw
    padded = raw + zlib.crc32(raw).to_bytes(4, "little")[:2]
    words = []
    for i in range(0, len(padded), 3):
        n = int.from_bytes(padded[i:i + 3], "big")
        words += [WORDS[n >> 12], WORDS[n & 0xFFF]]
    return " ".join(words)


def key_from_recovery(text: str) -> Masterkey:
    """The master key in a recovery key. Raises VaultError on an unknown word or a wrong checksum."""
    words = text.lower().split()
    if len(words) != 44:
        raise VaultError(f"A recovery key has 44 words; this has {len(words)}.")
    unknown = [w for w in words if w not in INDEX]
    if unknown:
        raise VaultError(f"Not a recovery key word: {unknown[0]!r}. Check the spelling.")
    data = b"".join(((INDEX[words[i]] << 12) | INDEX[words[i + 1]]).to_bytes(3, "big") for i in range(0, 44, 2))
    raw, check = data[:64], data[64:66]
    if zlib.crc32(raw).to_bytes(4, "little")[:2] != check:
        raise VaultError("This recovery key doesn't check out: a word is wrong or in the wrong place.")
    return Masterkey(bytearray(raw[:32]), bytearray(raw[32:]))


# ---------------------------------------------------------------- passwords

def check_new_password(password: str, again: str | None = None) -> None:
    if len(password) < MIN_PASSWORD:
        raise VaultError(f"Choose a password of at least {MIN_PASSWORD} characters.")
    if again is not None and again != password:
        raise VaultError("The two passwords don't match.")


def _write_key_file(folder: Path, key: Masterkey, password: str) -> None:
    from .writer import _write_atomic
    _write_atomic(folder / "masterkey.cryptomator", write_masterkey_file(key, password, os.urandom(32)))


def change_password(folder: Path, old: str, new: str) -> None:
    """Re-wrap the master key with a new password. Raises WrongPassword if the old one is wrong."""
    from .keys import unlock_masterkey
    folder = Path(folder)
    check_new_password(new)
    key = unlock_masterkey((folder / "masterkey.cryptomator").read_bytes(), old)
    try:
        verify_vault_config((folder / "vault.cryptomator").read_bytes(), key)
        _write_key_file(folder, key, new)
    finally:
        key.wipe()


def reset_password(folder: Path, recovery: str, new: str) -> None:
    """A new password from the recovery key, after checking the key really belongs to this vault."""
    folder = Path(folder)
    check_new_password(new)
    key = key_from_recovery(recovery)
    try:
        try:
            verify_vault_config((folder / "vault.cryptomator").read_bytes(), key)
        except VaultError:
            raise VaultError("This recovery key belongs to a different vault.")
        _write_key_file(folder, key, new)
    finally:
        key.wipe()


# ---------------------------------------------------------------- a new vault

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def create_vault(folder: Path, password: str) -> Masterkey:
    """A new, empty format 8 vault in folder (which must not exist yet, or be empty). Returns its key (wipe it)."""
    from .writer import _write_atomic
    folder = Path(folder).expanduser()
    check_new_password(password)
    if folder.exists() and any(folder.iterdir()):
        raise VaultError("That folder isn't empty. Choose a new folder for the vault.")
    if not folder.parent.is_dir():
        raise VaultError("The folder it goes in doesn't exist.")
    folder.mkdir(exist_ok=True)
    key = Masterkey(bytearray(os.urandom(32)), bytearray(os.urandom(32)))
    _write_key_file(folder, key, password)
    header = {"kid": "masterkeyfile:masterkey.cryptomator", "typ": "JWT", "alg": "HS256"}
    claims = {"jti": str(uuid.uuid4()), "format": 8, "cipherCombo": "SIV_GCM", "shorteningThreshold": 220}
    signing = _b64url(json.dumps(header, separators=(",", ":")).encode()) + "." + \
        _b64url(json.dumps(claims, separators=(",", ":")).encode())
    sig = hmac.new(key.raw, signing.encode(), hashlib.sha256).digest()
    _write_atomic(folder / "vault.cryptomator", (signing + "." + _b64url(sig)).encode())
    config = verify_vault_config((folder / "vault.cryptomator").read_bytes(), key)
    names = Names(key, config.shortening_threshold)
    xx, rest = names.dir_path(ROOT_DIR_ID)
    root = folder / "d" / xx / rest
    root.mkdir(parents=True)
    _write_atomic(root / "dirid.c9r", Content(key, config.cipher_combo).encrypt(ROOT_DIR_ID))
    return key
