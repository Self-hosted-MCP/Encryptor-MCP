# SPDX-License-Identifier: AGPL-3.0-only
"""Test vaults made by Cryptomator's own libraries (tests/java/RefVault.java), and the official reader as a judge.

The fixtures in tests/fixtures/ were made with cryptofs 2.10.0 and cryptolib 2.2.2 from Cryptomator 1.19.3, with
test passwords only. Tests that run the official code need a JDK and Cryptomator.app; they're skipped otherwise.
"""
import base64
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from encryptor_mcp.vault import keys, tree

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
MODES = ("SIV_GCM", "SIV_CTRMAC")
CRYPTOMATOR_MODS = Path(os.environ.get("CRYPTOMATOR_MODS", "/Applications/Cryptomator.app/Contents/app/mods"))


def password(mode: str) -> str:
    return f"test-password-{mode}"


def java() -> str | None:
    found = sorted((ROOT.parent / ".tools").glob("jdk-*/Contents/Home/bin/java")) or sorted((ROOT.parent / ".tools").glob("jdk-*/bin/java"))
    return str(found[-1]) if found else shutil.which("java")


def official(*args: str) -> list[str]:
    """Runs RefVault.java with Cryptomator's libraries; returns its entry lines."""
    j = java()
    if not j or not CRYPTOMATOR_MODS.is_dir():
        if os.environ.get("REQUIRE_REFERENCE"):   # in CI the reference must run, never be skipped quietly
            pytest.fail("the official reference (a JDK and Cryptomator's libraries) is required here")
        pytest.skip("needs a JDK and Cryptomator.app (or tests/java/fetch_jars.py) for the official reference")
    # non-ASCII arguments go base64-encoded and the output comes back as UTF-8, so names survive on Windows too
    safe = [a if a.isascii() else "b64:" + base64.b64encode(a.encode()).decode() for a in args]
    out = subprocess.run([j, "-cp", f"{CRYPTOMATOR_MODS}/*", str(ROOT / "java" / "RefVault.java"), *safe],
                         capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    return sorted(line for line in out.stdout.splitlines() if line.split("\t")[0] in ("dir", "file", "link"))


@pytest.fixture(params=MODES)
def vault(request, tmp_path):
    """A fresh copy of a reference vault: (path, mode)."""
    path = tmp_path / f"vault-{request.param}"
    shutil.copytree(FIXTURES / f"vault-{request.param}", path)
    return path, request.param


def open_tree(path: Path, mode: str) -> tree.Tree:
    key = keys.unlock_masterkey((path / "masterkey.cryptomator").read_bytes(), password(mode))
    return tree.Tree(path, key, keys.verify_vault_config((path / "vault.cryptomator").read_bytes(), key))
