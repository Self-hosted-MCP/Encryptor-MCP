# SPDX-License-Identifier: AGPL-3.0-only
"""The Finder mount's WebDAV server, its guards, and mounting/unmounting (macOS commands faked here; the real
mount was checked by hand in Finder)."""
import shutil
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

import pytest

from conftest import FIXTURES, official, open_tree, password
from test_vault import ours
from encryptor_mcp import mount, unlock as U
from encryptor_mcp.changes import Journal

PW = "test-password-SIV_GCM"


@pytest.fixture
def dav(tmp_path, monkeypatch):
    v = tmp_path / "v"
    shutil.copytree(FIXTURES / "vault-SIV_GCM", v)
    m = U.UnlockManager([U.VaultSpec("My Vault", v)])
    s = m.unlock(m.request_unlock("My Vault"), PW)
    j = Journal(s.tree)
    monkeypatch.setattr(mount, "same_user", lambda local, client: True)
    mt = mount.serve(s, j, m)
    yield m, s, j, mt, v
    mt.server.stop()


def req(url, method="GET", data=None, headers=None, host=None):
    r = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if host:
        r.add_header("Host", host)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except ConnectionError:   # Windows: the server refused and closed before the body was sent
        return 0, b""


def test_reads_like_the_vault(dav):
    m, s, j, mt, v = dav
    status, body = req(mt.url, "PROPFIND", headers={"Depth": "1"})
    assert status == 207 and b"Folder%20A" in body and b".encryptor" not in body and b"metadata_never_index" not in body
    assert req(mt.url + "hello.txt") == (200, b"Hello from Cryptomator's own code.\n")
    nfd = "Folder%20A/Sub%20folder/notes%20u%CC%88%20e%CC%81%20%E6%97%A5%E6%9C%AC.txt"   # how macOS spells ü é
    assert req(mt.url + nfd)[0] == 200
    assert req(mt.url + ".metadata_never_index")[0] == 200     # asks Spotlight not to index
    assert req(mt.url + ".encryptor/changes")[0] == 404


def test_guards(dav, monkeypatch):
    m, s, j, mt, v = dav
    base = mt.url.split("/" + mt.secret)[0]
    assert req(mt.url, "PROPFIND", host="evil.example")[0] == 421
    assert req(base + "/v/", "PROPFIND")[0] == 404                       # without the secret
    assert req(base + "/wrong-secret/v/", "PROPFIND")[0] == 404
    monkeypatch.setattr(mount, "same_user", lambda local, client: False)
    assert req(mt.url + "?x", "PROPFIND")[0] in (207, 403)              # a trusted connection may be reused
    mt2 = mount.serve(s, j, m)
    try:
        assert req(mt2.url, "PROPFIND")[0] == 403                       # another user's program
    finally:
        mt2.server.stop()


def test_changes_go_through_the_log_and_trash(dav):
    m, s, j, mt, v = dav
    assert req(mt.url + "new.txt", "PUT", b"from finder")[0] == 201
    assert req(mt.url + "new.txt", "PUT", b"saved again")[0] == 204
    assert req(mt.url + "._new.txt", "PUT", b"\0apple")[0] == 201      # Finder's own file: memory only
    assert req(mt.url + ".DS_Store", "PUT", b"ds")[0] == 201
    assert req(mt.url + "tmp.sb", "PUT", b"atomic save")[0] == 201
    assert req(mt.url + "tmp.sb", "MOVE", headers={"Destination": mt.url + "new.txt", "Overwrite": "T"})[0] == 204
    assert req(mt.url + "Made%20here", "MKCOL")[0] == 201
    assert req(mt.url + "Folder%20A", "COPY", headers={"Destination": mt.url + "Made%20here/A", "Depth": "infinity"})[0] in (201, 204)
    assert req(mt.url + "big.bin", "DELETE")[0] == 204
    assert req(mt.url + "new.txt") == (200, b"atomic save")
    assert [r["path"] for r in j.trash_items()] == ["/big.bin"]
    assert {r["app"] for r in j.records(50)} == {"Finder"} and len(j.versions("/new.txt")) == 3
    t = open_tree(v, "SIV_GCM")
    assert not any(e.name.startswith("._") or e.name == ".DS_Store" for _, e in t.walk())
    assert t.read_file(t.resolve("/Made here/A/Sub folder/notes ü é 日本.txt")).startswith(b"Unicode")
    assert ours(t) == official("dump", str(v), password("SIV_GCM"))
    j.undo("", "test", "")      # the delete, done outside the mount: Finder sees it within the 2-second cache
    mt.provider.changed()
    assert req(mt.url + "big.bin")[0] == 200


def test_read_only_and_locked(dav, tmp_path):
    m, s, j, mt, v = dav
    s.read_only = True
    ro = mount.serve(s, j, m)
    try:
        assert req(ro.url + "x.txt", "PUT", b"x")[0] in (0, 403, 405)
        assert req(ro.url + "hello.txt", "DELETE")[0] in (0, 403, 405)
        t = open_tree(v, "SIV_GCM")
        assert t.resolve("/hello.txt") and "x.txt" not in [e.name for e in t.list_dir(b"")]
        assert req(ro.url + "hello.txt")[0] == 200
    finally:
        ro.server.stop()
    m.lock("My Vault")
    assert req(mt.url, "PROPFIND")[0] == 404


@pytest.mark.skipif(sys.platform == "win32", reason="the Finder mount is macOS only")
def test_same_user_check(monkeypatch):
    calls = []

    def fake(cmd, **kw):
        calls.append(cmd)
        if cmd[0] == "pgrep":
            return subprocess.CompletedProcess(cmd, 0, "4242\n", "")
        return subprocess.CompletedProcess(cmd, 0, "p4242\nf5\nn127.0.0.1:50001->127.0.0.1:40000\n", "")
    assert mount.same_user(40000, 50001, run=fake)
    assert "-b" in calls[1] and "-p" in calls[1]          # never looks into mounted volumes
    assert not mount.same_user(40000, 50002, run=fake)     # some other program's connection
    none = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "")
    assert not mount.same_user(40000, 50001, run=none)     # no mount agent of this user


def test_mount_and_unmount_on_lock(tmp_path, monkeypatch):
    v = tmp_path / "v"
    shutil.copytree(FIXTURES / "vault-SIV_GCM", v)
    m = U.UnlockManager([U.VaultSpec("My Vault", v)])
    s = m.unlock(m.request_unlock("My Vault"), PW)
    ran, mounted = [], {}

    def fake(cmd, **kw):
        ran.append(cmd[0])
        if cmd[0] == "mount_webdav":
            mounted["line"] = f"{cmd[-2]} on {cmd[-1]} (webdav, nodev)"
        if cmd[0] in ("diskutil", "umount"):
            mounted.pop("line", None)
        if cmd[0] == "mount":
            return subprocess.CompletedProcess(cmd, 0, mounted.get("line", ""), "")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(mount.sys, "platform", "darwin")
    monkeypatch.setattr(mount.shutil, "which", lambda name: "/sbin/" + name)
    ms = mount.Mounts(m, lambda s: Journal(s.tree), tmp_path / "mounts", run=fake)
    where = ms.mount(s)
    assert Path(where) == tmp_path / "mounts" / "My Vault" and ms.where("My Vault") == where and "open" in ran
    assert ms.mount(s) == where                             # a second click reuses it
    m.lock("My Vault", "locked: no use")                    # locking removes it (in a background thread)
    import time
    for _ in range(50):
        if not ms.active and not (tmp_path / "mounts" / "My Vault").exists():
            break
        time.sleep(0.1)
    assert not ms.active and "diskutil" in ran and not (tmp_path / "mounts" / "My Vault").exists()


def test_secret_address_never_logged(dav, caplog, capfd):
    import logging
    m, s, j, mt, v = dav
    caplog.set_level(logging.DEBUG)
    mt2 = mount.serve(s, j, m)
    req(mt2.url, "PROPFIND")
    req(mt2.url + "missing", "GET")
    mt2.server.stop()
    out, err = capfd.readouterr()
    assert mt2.secret not in caplog.text and mt2.secret not in out + err
