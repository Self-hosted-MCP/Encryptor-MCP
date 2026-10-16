# SPDX-License-Identifier: AGPL-3.0-only
"""The vault's two keys, and the two files that hold the vault's settings.

masterkey.cryptomator (JSON): the encryption key and the MAC key, each wrapped (RFC 3394) with a key made from the
password by scrypt. vault.cryptomator (a JWT): format, cipher mode and name length limit, signed with both keys.
Both files are read as untrusted input: sizes, fields and values are checked before anything is used.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import unicodedata
from dataclasses import dataclass

from cryptography.hazmat.primitives.keywrap import InvalidUnwrap, aes_key_unwrap, aes_key_wrap

MAX_CONFIG_BYTES = 64 * 1024      # both files are a few hundred bytes; anything bigger is refused
SUPPORTED_FORMAT = 8
CIPHER_COMBOS = ("SIV_GCM", "SIV_CTRMAC")
JWT_ALGS = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}
KID_MASTERKEY_PREFIX = "masterkeyfile:"


class VaultError(Exception):
    """A problem with a vault, in plain words. Never contains a password or a key."""


class WrongPassword(VaultError):
    pass


@dataclass
class Masterkey:
    """The two 32-byte keys. Kept in bytearrays so they can be overwritten when the vault locks."""
    enc: bytearray
    mac: bytearray

    @property
    def raw(self) -> bytes:
        """enc || mac: the 64-byte key that signs vault.cryptomator."""
        return bytes(self.enc) + bytes(self.mac)

    def wipe(self) -> None:
        for buf in (self.enc, self.mac):
            for i in range(len(buf)):
                buf[i] = 0


def b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def normalize_password(password: str) -> bytes:
    """Passwords are NFC-normalised and UTF-8 encoded, like Cryptomator does since format 6."""
    return unicodedata.normalize("NFC", password).encode("utf-8")


def _check_size(data: bytes, what: str) -> None:
    if len(data) > MAX_CONFIG_BYTES:
        raise VaultError(f"{what} is too large to be a vault file.")


# ---------------------------------------------------------------- masterkey.cryptomator

def parse_masterkey_file(data: bytes) -> dict:
    _check_size(data, "masterkey.cryptomator")
    try:
        mk = json.loads(data)
    except ValueError:
        raise VaultError("masterkey.cryptomator isn't valid JSON.")
    if not isinstance(mk, dict):
        raise VaultError("masterkey.cryptomator has an unexpected shape.")
    for field, kind in (("scryptSalt", str), ("scryptCostParam", int), ("scryptBlockSize", int),
                        ("primaryMasterKey", str), ("hmacMasterKey", str), ("versionMac", str), ("version", int)):
        if not isinstance(mk.get(field), kind) or isinstance(mk.get(field), bool):
            raise VaultError(f"masterkey.cryptomator: '{field}' is missing or has the wrong type.")
    n, r = mk["scryptCostParam"], mk["scryptBlockSize"]
    # scrypt needs N to be a power of two; very large values would make unlocking hang or run out of memory
    if n < 2 or n & (n - 1) or n > 2 ** 20 or not 1 <= r <= 32:
        raise VaultError("masterkey.cryptomator: the scrypt settings are outside what Cryptomator uses.")
    return mk


def kek_from_password(password: str, mk: dict) -> bytes:
    n, r = mk["scryptCostParam"], mk["scryptBlockSize"]
    return hashlib.scrypt(normalize_password(password), salt=b64decode(mk["scryptSalt"]), n=n, r=r, p=1,
                          maxmem=128 * n * r * 2 + 1024 * 1024, dklen=32)


def unlock_masterkey(data: bytes, password: str) -> Masterkey:
    """Unwraps the two keys with the password. Raises WrongPassword if it doesn't fit."""
    mk = parse_masterkey_file(data)
    kek = kek_from_password(password, mk)
    try:
        enc = aes_key_unwrap(kek, b64decode(mk["primaryMasterKey"]))
        mac = aes_key_unwrap(kek, b64decode(mk["hmacMasterKey"]))
    except InvalidUnwrap:
        raise WrongPassword("Wrong password for this vault.")
    except ValueError:
        raise VaultError("masterkey.cryptomator: a wrapped key has the wrong length.")
    if len(enc) != 32 or len(mac) != 32:
        raise VaultError("masterkey.cryptomator: a key has the wrong length.")
    expected = hmac.new(mac, mk["version"].to_bytes(4, "big"), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, b64decode(mk["versionMac"])):
        raise VaultError("masterkey.cryptomator: the version check failed (the file may have been changed).")
    return Masterkey(bytearray(enc), bytearray(mac))


def write_masterkey_file(key: Masterkey, password: str, salt: bytes, n: int = 32768, r: int = 8,
                         version: int = 999) -> bytes:
    """A masterkey.cryptomator for these keys and this password (used to create vaults and change passwords)."""
    mk = {"scryptSalt": base64.b64encode(salt).decode(), "scryptCostParam": n, "scryptBlockSize": r}
    kek = kek_from_password(password, {**mk})
    out = {
        "version": version,
        **mk,
        "primaryMasterKey": base64.b64encode(aes_key_wrap(kek, bytes(key.enc))).decode(),
        "hmacMasterKey": base64.b64encode(aes_key_wrap(kek, bytes(key.mac))).decode(),
        "versionMac": base64.b64encode(
            hmac.new(bytes(key.mac), version.to_bytes(4, "big"), hashlib.sha256).digest()).decode(),
    }
    return json.dumps(out, indent=2).encode()


# ---------------------------------------------------------------- vault.cryptomator

@dataclass
class VaultConfig:
    format: int
    cipher_combo: str
    shortening_threshold: int
    vault_id: str
    kid: str
    alg: str


def read_vault_config_unverified(data: bytes) -> tuple[VaultConfig, bytes, bytes]:
    """Splits and checks the JWT without its signature: (config, signed part, signature). Verify before trusting."""
    _check_size(data, "vault.cryptomator")
    try:
        text = data.decode("ascii").strip()
        head_b64, claims_b64, sig_b64 = text.split(".")
        header = json.loads(b64url_decode(head_b64))
        claims = json.loads(b64url_decode(claims_b64))
        sig = b64url_decode(sig_b64)
    except (ValueError, UnicodeDecodeError):
        raise VaultError("vault.cryptomator isn't a valid signed settings file.")
    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise VaultError("vault.cryptomator has an unexpected shape.")
    alg, kid = header.get("alg"), header.get("kid")
    if alg not in JWT_ALGS:
        raise VaultError("vault.cryptomator uses a signature this tool doesn't accept.")
    if not isinstance(kid, str):
        raise VaultError("vault.cryptomator doesn't say where its key is.")
    if kid.startswith("hub+"):
        raise VaultError("This is a Cryptomator Hub vault. Hub vaults aren't supported yet.")
    if kid != KID_MASTERKEY_PREFIX + "masterkey.cryptomator":
        # Only the standard key file next to the config: never a path the file itself points to
        raise VaultError("vault.cryptomator points to a key location this tool doesn't accept.")
    fmt, combo, threshold, jti = (claims.get("format"), claims.get("cipherCombo"),
                                  claims.get("shorteningThreshold"), claims.get("jti"))
    if fmt != SUPPORTED_FORMAT:
        raise VaultError(f"This vault uses format {fmt!r}; this tool reads format {SUPPORTED_FORMAT}.")
    if combo not in CIPHER_COMBOS:
        raise VaultError(f"This vault uses the cipher mode {combo!r}, which this tool doesn't know.")
    if not isinstance(threshold, int) or isinstance(threshold, bool) or not 36 <= threshold <= 220:
        raise VaultError("vault.cryptomator: the name length limit is outside what Cryptomator allows.")
    if not isinstance(jti, str) or len(jti) > 100:
        raise VaultError("vault.cryptomator: the vault ID is missing or too long.")
    signed = f"{head_b64}.{claims_b64}".encode("ascii")
    return VaultConfig(fmt, combo, threshold, jti, kid, alg), signed, sig


def verify_vault_config(data: bytes, key: Masterkey) -> VaultConfig:
    config, signed, sig = read_vault_config_unverified(data)
    expected = hmac.new(key.raw, signed, JWT_ALGS[config.alg]).digest()
    if not hmac.compare_digest(expected, sig):
        raise VaultError("vault.cryptomator's signature doesn't match this vault's keys (the file may have been changed).")
    return config
