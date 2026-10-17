# SPDX-License-Identifier: AGPL-3.0-only
"""File contents: a header holding a fresh key for the file, then 32 KiB chunks, each encrypted and checked.

SIV_GCM:    header = nonce(12) | AES-GCM(encKey; 8 x 0xFF | content key(32)) | tag(16)              = 68 bytes
            chunk  = nonce(12) | AES-GCM(contentKey, aad = chunk number(8, big-endian) | header nonce) | tag(16)
SIV_CTRMAC: header = nonce(16) | AES-CTR(encKey, iv = nonce; 8 x 0xFF | content key(32))
                     | HMAC-SHA256(macKey; nonce | encrypted payload)                               = 88 bytes
            chunk  = nonce(16) | AES-CTR(contentKey, iv = nonce)
                     | HMAC-SHA256(macKey; header nonce | chunk number(8, big-endian) | nonce | ciphertext)
Empty content is written as the header plus one empty chunk, as Cryptomator does (checked on a vault made by
Cryptomator 1.19.3: an empty dirid.c9r is 68 + 28 bytes); a header alone is also read as empty. Every chunk is
checked before any of its bytes are returned.
"""

from __future__ import annotations

import hashlib
import hmac
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .keys import Masterkey, VaultError

CLEAR_CHUNK = 32 * 1024
RESERVED = b"\xff" * 8


class Corrupted(VaultError):
    """The data doesn't check out: changed, cut, or not from this vault."""


def _ctr(key: bytes, nonce: bytes) -> Cipher:
    return Cipher(algorithms.AES(key), modes.CTR(nonce))


class _Gcm:
    header_size = 68
    nonce_size = 12
    overhead = 12 + 16

    def __init__(self, key: Masterkey):
        self.key = key

    def header(self, content_key: bytes, nonce: bytes) -> bytes:
        return nonce + AESGCM(bytes(self.key.enc)).encrypt(nonce, RESERVED + content_key, None)

    def open_header(self, header: bytes) -> tuple[bytes, bytes]:
        nonce = header[:12]
        try:
            payload = AESGCM(bytes(self.key.enc)).decrypt(nonce, header[12:68], None)
        except InvalidTag:
            raise Corrupted("The file's header doesn't check out (changed, or from another vault).")
        return nonce, payload[8:]

    def seal(self, content_key: bytes, header_nonce: bytes, index: int, clear: bytes) -> bytes:
        nonce = os.urandom(12)
        aad = index.to_bytes(8, "big") + header_nonce
        return nonce + AESGCM(content_key).encrypt(nonce, clear, aad)

    def open(self, content_key: bytes, header_nonce: bytes, index: int, chunk: bytes) -> bytes:
        aad = index.to_bytes(8, "big") + header_nonce
        try:
            return AESGCM(content_key).decrypt(chunk[:12], chunk[12:], aad)
        except InvalidTag:
            raise Corrupted(f"Part {index + 1} of the file doesn't check out (changed or damaged).")


class _CtrMac:
    header_size = 88
    nonce_size = 16
    overhead = 16 + 32

    def __init__(self, key: Masterkey):
        self.key = key

    def header(self, content_key: bytes, nonce: bytes) -> bytes:
        enc = _ctr(bytes(self.key.enc), nonce).encryptor()
        ct = enc.update(RESERVED + content_key) + enc.finalize()
        mac = hmac.new(bytes(self.key.mac), nonce + ct, hashlib.sha256).digest()
        return nonce + ct + mac

    def open_header(self, header: bytes) -> tuple[bytes, bytes]:
        nonce, ct, mac = header[:16], header[16:56], header[56:88]
        expected = hmac.new(bytes(self.key.mac), nonce + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, mac):
            raise Corrupted("The file's header doesn't check out (changed, or from another vault).")
        dec = _ctr(bytes(self.key.enc), nonce).decryptor()
        payload = dec.update(ct) + dec.finalize()
        return nonce, payload[8:]

    def seal(self, content_key: bytes, header_nonce: bytes, index: int, clear: bytes) -> bytes:
        nonce = os.urandom(16)
        enc = _ctr(content_key, nonce).encryptor()
        ct = enc.update(clear) + enc.finalize()
        mac = hmac.new(bytes(self.key.mac), header_nonce + index.to_bytes(8, "big") + nonce + ct, hashlib.sha256).digest()
        return nonce + ct + mac

    def open(self, content_key: bytes, header_nonce: bytes, index: int, chunk: bytes) -> bytes:
        nonce, ct, mac = chunk[:16], chunk[16:-32], chunk[-32:]
        expected = hmac.new(bytes(self.key.mac), header_nonce + index.to_bytes(8, "big") + nonce + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, mac):
            raise Corrupted(f"Part {index + 1} of the file doesn't check out (changed or damaged).")
        dec = _ctr(content_key, nonce).decryptor()
        return dec.update(ct) + dec.finalize()


class Content:
    """Encrypts and decrypts whole files for one vault and cipher mode."""

    def __init__(self, key: Masterkey, cipher_combo: str):
        if cipher_combo == "SIV_GCM":
            self._c = _Gcm(key)
        elif cipher_combo == "SIV_CTRMAC":
            self._c = _CtrMac(key)
        else:
            raise VaultError(f"Unknown cipher mode {cipher_combo!r}.")
        self.chunk_size = CLEAR_CHUNK + self._c.overhead

    def cleartext_size(self, ciphertext_size: int) -> int:
        """The clear size from the encrypted size (header included). Raises Corrupted for impossible sizes."""
        body = ciphertext_size - self._c.header_size
        if body < 0:
            raise Corrupted("Too short to be an encrypted file.")
        full, rem = divmod(body, self.chunk_size)
        if 0 < rem < self._c.overhead:
            raise Corrupted("The file's size is impossible for an encrypted file (it may be cut).")
        return full * CLEAR_CHUNK + (rem - self._c.overhead if rem else 0)

    def decrypt(self, data: bytes) -> bytes:
        self.cleartext_size(len(data))
        nonce, content_key = self._c.open_header(data[:self._c.header_size])
        out = bytearray()
        body = memoryview(data)[self._c.header_size:]
        for index, start in enumerate(range(0, len(body), self.chunk_size)):
            out += self._c.open(content_key, nonce, index, bytes(body[start:start + self.chunk_size]))
        return bytes(out)

    def check_ends(self, path) -> None:
        """Opens a file's header and its last part without reading the rest: catches changed headers and files cut
        inside their last part. (A file cut exactly between parts looks whole; the fingerprint list catches that.)
        Raises Corrupted."""
        size = path.stat().st_size
        self.cleartext_size(size)
        with open(path, "rb") as f:
            nonce, content_key = self._c.open_header(f.read(self._c.header_size))
            body = size - self._c.header_size
            if body <= 0:
                return
            last = (body - 1) // self.chunk_size
            f.seek(self._c.header_size + last * self.chunk_size)
            self._c.open(content_key, nonce, last, f.read(self.chunk_size))

    def encrypt(self, clear: bytes) -> bytes:
        content_key = os.urandom(32)
        nonce = os.urandom(self._c.nonce_size)
        out = bytearray(self._c.header(content_key, nonce))
        for index, start in enumerate(range(0, max(len(clear), 1), CLEAR_CHUNK)):
            out += self._c.seal(content_key, nonce, index, clear[start:start + CLEAR_CHUNK])
        return bytes(out)
