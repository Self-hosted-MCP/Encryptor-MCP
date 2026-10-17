# SPDX-License-Identifier: AGPL-3.0-only
"""The health check, judged against Cryptomator's own health check, and its safe repairs."""
import shutil

import pytest

import damage
from conftest import FIXTURES, official, open_tree, password
from test_vault import ours
from encryptor_mcp.vault import health
from encryptor_mcp.vault.writer import _write_atomic


def cryptomator_kinds(path, mode):
    return {line.split("\t")[2] for line in official("health", str(path), password(mode))}


def test_healthy_vaults(vault):
    path, mode = vault
    assert health.check(open_tree(path, mode)) == [] and cryptomator_kinds(path, mode) == set()


@pytest.mark.parametrize("breakage", damage.ALL, ids=lambda f: f.__name__)
def test_finds_what_cryptomator_finds(vault, breakage):
    path, mode = vault
    breakage(open_tree(path, mode))
    mine = {f.kind for f in health.check(open_tree(path, mode))}
    theirs = cryptomator_kinds(path, mode)
    assert theirs and theirs <= mine, (theirs, mine)


def test_own_extra_checks(vault):
    path, mode = vault
    t = open_tree(path, mode)
    hello = t.contents_path(t.resolve("/hello.txt"))
    data = bytearray(hello.read_bytes())
    data[20] ^= 1                                               # a changed header
    hello.write_bytes(bytes(data))
    big = t.contents_path(t.resolve("/big.bin"))
    big.write_bytes(big.read_bytes()[:-5])                      # cut mid-chunk
    (t.dir_location(b"") / ".encryptor-0123.tmp").write_bytes(b"x")
    shutil.copy(t.resolve("/empty.txt").stored, t.dir_location(b"") / "empty (1).c9r")
    kinds = {(f.kind, f.where) for f in health.check(open_tree(path, mode))}
    assert ("DamagedFile", "/hello.txt") in kinds and ("DamagedFile", "/big.bin") in kinds
    assert {k for k, _ in kinds} >= {"LeftoverTempFile", "ConflictCopy"}


@pytest.mark.parametrize("breakage", [damage.missing_dirid_backup, damage.missing_content_dir,
                                      damage.orphan_content_dir, damage.mismatched_long_name],
                         ids=lambda f: f.__name__)
def test_repairs_leave_a_vault_cryptomator_calls_healthy(vault, breakage):
    path, mode = vault
    breakage(open_tree(path, mode))
    t = open_tree(path, mode)
    for f in health.check(t):
        assert f.kind in health.FIXABLE and f.fix
        health.repair(t, f)
    assert health.check(open_tree(path, mode)) == [] and cryptomator_kinds(path, mode) == set()
    assert ours(open_tree(path, mode)) == official("dump", str(path), password(mode))


def test_orphans_come_back_as_recovered(vault):
    path, mode = vault
    damage.orphan_content_dir(open_tree(path, mode))
    t = open_tree(path, mode)
    for f in health.check(t):
        health.repair(t, f)
    t = open_tree(path, mode)
    assert t.read_file(t.resolve("/Recovered/notes ü é 日本.txt")).startswith(b"Unicode")


def test_no_repair_without_a_safe_one(vault):
    path, mode = vault
    damage.unknown_type(open_tree(path, mode))
    t = open_tree(path, mode)
    f = health.check(t)[0]
    assert f.kind == "UnknownType" and not f.fix
    with pytest.raises(Exception, match="no safe automatic repair"):
        health.repair(t, f)


def test_health_on_the_vault_page_and_for_the_ai(tmp_path, monkeypatch):
    """The check and the confirmed repair through the control center; the AI tool only reports."""
    from test_center import _wsgi
    from starlette.testclient import TestClient
    from encryptor_mcp import server, unlock as U, web
    from encryptor_mcp.changes import Journal
    v = tmp_path / "v"
    shutil.copytree(FIXTURES / "vault-SIV_GCM", v)
    damage.missing_dirid_backup(open_tree(v, "SIV_GCM"))
    m = U.UnlockManager([U.VaultSpec("V", v)])
    s = m.unlock(m.request_unlock("V"), password("SIV_GCM"))
    center = web.Center(lambda s: Journal(s.tree), lambda: {"vaults": []}, lambda k, f: "")
    site = web.Site(m, "http://127.0.0.1:1", None, center)
    client = TestClient(_wsgi(site), base_url="http://127.0.0.1:1")
    o = {"origin": "http://127.0.0.1:1"}
    base = f"/vault/{s.status_code}"
    assert "Check health" in client.get(base).text
    r = client.post(base + "/health", headers=o)
    assert "Found 1 thing" in r.text and "Harmless" in r.text and "Repair 1 safely" in r.text
    r = client.post(base + "/repair", headers=o)
    assert "Repair V?" in r.text and "Yes, repair 1" in r.text                 # asked first
    assert health.check(s.tree)                                                  # nothing done yet
    r = client.post(base + "/repair", data={"confirm": "yes"}, headers=o)
    assert "Wrote the folder ID backup" in r.text and health.check(s.tree) == []
    monkeypatch.setattr(server, "_manager", m)
    assert "is healthy" in server.health_check("V")
