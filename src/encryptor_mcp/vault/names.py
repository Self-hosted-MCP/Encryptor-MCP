# SPDX-License-Identifier: AGPL-3.0-only
"""Encrypted names and folder paths.

Names: AES-SIV over the NFC-normalised UTF-8 name, with the parent folder's ID as associated data, Base64url (with
padding) plus ".c9r". Names longer than the vault's limit are shortened to Base64url(SHA-1(full name)) + ".c9s".
Folders live flat under d/: Base32(SHA-1(AES-SIV(folder ID))) split as d/XX/YYYY.... The root folder's ID is empty.
AES-SIV takes the MAC key first, then the encryption key (RFC 5297 order).
"""

from __future__ import annotations

import base64
import hashlib
import unicodedata

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESSIV

from .keys import Masterkey, VaultError

C9R = ".c9r"
C9S = ".c9s"
ROOT_DIR_ID = b""
MAX_DIR_ID_LENGTH = 36
MIN_CIPHER_NAME_LENGTH = 28


class Names:
    def __init__(self, key: Masterkey, shortening_threshold: int = 220):
        self._siv = AESSIV(bytes(key.mac) + bytes(key.enc))
        self.threshold = shortening_threshold

    def dir_path(self, dir_id: bytes) -> tuple[str, str]:
        """('d', 'XX', 'YYYY...') parts below the vault root for a folder ID: returned as ('XX', 'YYYY...')."""
        if len(dir_id) > MAX_DIR_ID_LENGTH:
            raise VaultError("A folder ID is longer than Cryptomator allows.")
        digest = hashlib.sha1(self._siv.encrypt(dir_id, None)).digest()
        hashed = base64.b32encode(digest).decode("ascii")
        return hashed[:2], hashed[2:]

    def encrypt(self, name: str, parent_dir_id: bytes) -> str:
        """The full encrypted name, with .c9r (not yet shortened)."""
        if not name or name in (".", "..") or "/" in name or "\x00" in name:
            raise VaultError(f"{name!r} isn't a valid file or folder name.")
        clear = unicodedata.normalize("NFC", name).encode("utf-8")
        return base64.urlsafe_b64encode(self._siv.encrypt(clear, [parent_dir_id])).decode("ascii") + C9R

    def decrypt(self, cipher_name: str, parent_dir_id: bytes) -> str:
        """The clear name from an encrypted name (with or without .c9r). Raises VaultError if it doesn't decrypt."""
        stem = cipher_name[:-len(C9R)] if cipher_name.endswith(C9R) else cipher_name
        if len(stem) < MIN_CIPHER_NAME_LENGTH - len(C9R):
            raise VaultError("Too short to be an encrypted name.")
        try:
            data = base64.urlsafe_b64decode(stem + "=" * (-len(stem) % 4))
            return self._siv.decrypt(data, [parent_dir_id]).decode("utf-8")
        except (ValueError, InvalidTag, UnicodeDecodeError):
            raise VaultError("This name doesn't decrypt with this vault's keys in this folder.")

    def stored_name(self, full_cipher_name: str) -> tuple[str, bool]:
        """What the entry is called on disk: the full name, or the shortened .c9s name. (name, shortened?)"""
        if len(full_cipher_name) > self.threshold:
            digest = hashlib.sha1(full_cipher_name.encode("ascii")).digest()
            return base64.urlsafe_b64encode(digest).decode("ascii") + C9S, True
        return full_cipher_name, False
