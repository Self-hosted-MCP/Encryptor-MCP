# SPDX-License-Identifier: AGPL-3.0-only
"""Small files kept by Encryptor (logins, page settings): written whole and owner-only; secrets only as hashes."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
from pathlib import Path


def private_write(path: Path, text: str) -> None:
    """Writes the whole file at once, owner-only."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def hash_passphrase(passphrase: str, salt: bytes | None = None, rounds: int = 600_000) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, rounds)
    return f"pbkdf2:{rounds}:{salt.hex()}:{digest.hex()}"


def check_passphrase(passphrase: str, stored: str) -> bool:
    try:
        _, rounds, salt, _digest = stored.replace("$", ":").split(":")
        return hmac.compare_digest(hash_passphrase(passphrase, bytes.fromhex(salt), int(rounds)), stored.replace("$", ":"))
    except Exception:
        return False


def token_key(token: str) -> str:
    """Files keep only this fingerprint of each login token, so a copy of a file can't be used to log in."""
    return hashlib.sha256(token.encode()).hexdigest()
