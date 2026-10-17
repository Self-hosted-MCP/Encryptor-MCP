# SPDX-License-Identifier: AGPL-3.0-only
"""Unlocking and locking: one-time links, time limits, idle lock, wrong passwords, the local page, the box."""
import http.client
import subprocess
import time
from urllib.parse import urlencode

import pytest

from conftest import FIXTURES
from encryptor_mcp import ask, unlock as U, web

PW = "test-password-SIV_GCM"


@pytest.fixture
def clock():
    now = [1000.0]
    return now


@pytest.fixture
def m(clock):
    return U.UnlockManager([U.VaultSpec("Test", FIXTURES / "vault-SIV_GCM"),
                            U.VaultSpec("Ro", FIXTURES / "vault-SIV_CTRMAC", "read"),
                            U.VaultSpec("Secret", FIXTURES / "vault-SIV_GCM", "hidden")],
                           idle_minutes=10, max_hours=12, clock=lambda: clock[0])


def test_locked_until_unlocked(m):
    with pytest.raises(U.Locked, match="Call unlock"):
        m.use("Test")
    s = m.unlock(m.request_unlock("Test", "Claude", "notes"), PW)
    assert m.use("Test") is s and s.app == "Claude" and s.purpose == "notes"


def test_hidden_vault_is_invisible(m):
    with pytest.raises(U.UnlockRefused, match="No vault"):
        m.request_unlock("Secret")


def test_read_mode_vault_opens_read_only(m):
    assert m.unlock(m.request_unlock("Ro"), "test-password-SIV_CTRMAC").read_only


def test_link_once_and_expiring(m, clock):
    code = m.request_unlock("Test")
    m.unlock(code, PW)
    with pytest.raises(U.UnlockRefused, match="expired or was already used"):
        m.unlock(code, PW)
    late = m.request_unlock("Test")
    clock[0] += 301
    with pytest.raises(U.UnlockRefused, match="expired"):
        m.unlock(late, PW)


def test_idle_lock_and_activity(m, clock):
    s = m.unlock(m.request_unlock("Test"), PW)
    clock[0] += 9 * 60
    m.use("Test")
    clock[0] += 9 * 60
    m.sweep()
    assert m.status("Test")
    clock[0] += 11 * 60
    m.sweep()
    assert m.status("Test") is None and set(s.key.enc) == {0}


def test_chosen_time_and_hard_limit(m, clock):
    m.unlock(m.request_unlock("Test"), PW, keep="15m")
    for _ in range(2):
        clock[0] += 5 * 60
        m.use("Test")
    clock[0] += 5 * 60
    with pytest.raises(U.Locked):
        m.use("Test")
    s = m.unlock(m.request_unlock("Test"), PW, keep="lock")
    for _ in range(13):
        clock[0] += 3600
        s.last_used = clock[0]
    m.sweep()
    assert m.status("Test") is None


def test_wrong_passwords_lock_out(m, clock):
    for i in range(5):
        with pytest.raises(U.UnlockRefused, match="Wrong password"):
            m.unlock(m.request_unlock("Test"), "nope")
    with pytest.raises(U.UnlockRefused, match="Try again in 15 minutes"):
        m.unlock(m.request_unlock("Test"), PW)
    clock[0] += 15 * 60 + 1
    assert m.unlock(m.request_unlock("Test"), PW)


def test_lock_now_and_lock_all_wipe_keys(m):
    s = m.unlock(m.request_unlock("Test"), PW)
    assert m.lock("Test") and set(s.key.enc) == {0} and not m.lock("Test")
    s1 = m.unlock(m.request_unlock("Test"), PW)
    s2 = m.unlock(m.request_unlock("Ro"), "test-password-SIV_CTRMAC")
    m.lock_all("stopped")
    assert not m.sessions and set(s1.key.mac) == {0} and set(s2.key.mac) == {0}


def test_events_never_hold_passwords(m):
    try:
        m.unlock(m.request_unlock("Test", "App", "why"), "a-wrong-secret")
    except U.UnlockRefused:
        pass
    m.unlock(m.request_unlock("Test"), PW)
    text = " ".join(e[2] for e in m.events)
    assert "a-wrong-secret" not in text and PW not in text and "wrong password" in text


# ---------------------------------------------------------------- the local page

@pytest.fixture
def page():
    mgr = U.UnlockManager([U.VaultSpec("Test", FIXTURES / "vault-SIV_GCM")])
    lp = web.LocalPages(mgr)
    yield mgr, lp
    lp.close()


def call(lp, method, path, form=None, host=None, origin="same"):
    c = http.client.HTTPConnection("127.0.0.1", lp.port, timeout=10)
    headers = {"Host": host or f"127.0.0.1:{lp.port}"}
    body = None
    if form is not None:
        body = urlencode(form)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        if origin:
            headers["Origin"] = lp.base if origin == "same" else origin
    c.request(method, path, body=body, headers=headers)
    r = c.getresponse()
    return r.status, dict(r.getheaders()), r.read().decode("utf-8", "replace")


def test_page_shows_who_and_why_without_scripts(page):
    mgr, lp = page
    code = mgr.request_unlock("Test", "Claude", "summarise <notes>")
    status, headers, body = call(lp, "GET", f"/unlock/{code}")
    assert status == 200 and "Claude" in body and "summarise &lt;notes&gt;" in body and "<script" not in body
    assert "default-src 'none'" in headers["Content-Security-Policy"] and headers["X-Frame-Options"] == "DENY"


def test_page_refuses_other_hosts_and_sites(page):
    mgr, lp = page
    code = mgr.request_unlock("Test")
    assert call(lp, "GET", f"/unlock/{code}", host="evil.example")[0] == 421
    assert call(lp, "POST", f"/unlock/{code}", {"password": PW}, origin="https://evil.example")[0] == 403
    assert mgr.status("Test") is None


def test_page_unlock_status_and_lock(page):
    mgr, lp = page
    code = mgr.request_unlock("Test", "Claude")
    t = time.time()
    status, _, body = call(lp, "POST", f"/unlock/{code}", {"password": "nope", "keep": "1h"})
    assert status == 401 and "Wrong password" in body and time.time() - t >= 0.9
    status, headers, _ = call(lp, "POST", f"/unlock/{code}", {"password": PW, "keep": "1h", "read_only": "yes"})
    assert status == 303 and mgr.status("Test").read_only
    status, _, body = call(lp, "GET", headers["Location"])
    assert "Read only" in body and "1 hour" in body and "locks after 10 minutes" in body and PW not in body
    assert call(lp, "GET", f"/unlock/{code}")[0] == 410
    key = mgr.status("Test").key
    assert call(lp, "POST", headers["Location"] + "/lock", {})[0] == 200
    assert mgr.status("Test") is None and set(key.enc) == {0}
    assert call(lp, "GET", headers["Location"])[0] == 404


def test_page_is_only_on_this_computer(page):
    _, lp = page
    assert lp.httpd.server_address[0] == "127.0.0.1"


# ---------------------------------------------------------------- the native box

def test_box_returns_the_typed_password_and_passes_text_as_arguments(monkeypatch):
    monkeypatch.setattr(ask.sys, "platform", "darwin")
    calls = []
    def fake(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "OK:typed pass\n", "")
    assert ask.password_box('V "x"', "App", "Why", run=fake) == "typed pass"
    assert calls[0][3:6] == ['V "x"', "App", "Why"] and 'V "x"' not in calls[0][2]


@pytest.mark.parametrize("answer", ["CANCEL:\n", "TIMEOUT:\n"])
def test_box_cancel_or_timeout(monkeypatch, answer):
    monkeypatch.setattr(ask.sys, "platform", "darwin")
    fake = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, answer, "")
    assert ask.password_box("V", "A", "P", run=fake) is None


# ---------------------------------------------------------------- the browse page

@pytest.fixture
def open_page(tmp_path):
    import shutil
    v = tmp_path / "v"
    shutil.copytree(FIXTURES / "vault-SIV_GCM", v)
    mgr = U.UnlockManager([U.VaultSpec("Test", v)])
    lp = web.LocalPages(mgr)
    s = mgr.unlock(mgr.request_unlock("Test"), PW)
    from encryptor_mcp.changes import Journal
    j = Journal(s.tree)
    j.write("/x <b>.html", b"<script>alert(1)</script>", "", "t", "")
    j.write("/pic.png", b"\x89PNG\r\n\x1a\n" + b"\0" * 20, "", "t", "")
    j.write("/doc.pdf", b"%PDF-1.4", "", "t", "")
    yield mgr, lp, f"/vault/{s.status_code}"
    lp.close()


def test_browse_lists_folders_and_hides_records(open_page):
    mgr, lp, base = open_page
    status, _, body = call(lp, "GET", base + "/files/")
    assert status == 200 and "Folder A" in body and ".encryptor" not in body and "x &lt;b&gt;.html" in body
    status, _, body = call(lp, "GET", base + "/files/Folder%20A/Sub%20folder/")
    assert "notes ü é 日本.txt" in body
    assert call(lp, "GET", base + "/files/.encryptor/")[0] == 404
    assert call(lp, "GET", base + "/files/Folder%20A/..%2F..%2F/")[0] == 404


def test_files_open_sandboxed_or_download(open_page):
    mgr, lp, base = open_page
    status, h, body = call(lp, "GET", base + "/open/x%20%3Cb%3E.html")
    assert status == 200 and h["Content-Type"].startswith("text/plain") and "sandbox" in h["Content-Security-Policy"]
    status, h, _ = call(lp, "GET", base + "/open/pic.png")
    assert h["Content-Type"] == "image/png" and "sandbox" in h["Content-Security-Policy"]
    assert "can&#x27;t be shown" in call(lp, "GET", base + "/open/doc.pdf")[2]
    status, h, _ = call(lp, "GET", base + "/get/Folder%20A/Sub%20folder/notes%20%C3%BC%20%C3%A9%20%E6%97%A5%E6%9C%AC.txt")
    assert h["Content-Disposition"].startswith("attachment;") and "UTF-8''notes%20%C3%BC" in h["Content-Disposition"]
    assert any("downloaded Folder A/Sub folder/notes" in e[2] for e in mgr.events)


def test_browse_needs_the_secret_and_an_open_vault(open_page):
    mgr, lp, base = open_page
    assert call(lp, "GET", "/vault/wrong/files/")[0] == 404
    mgr.lock("Test")
    assert call(lp, "GET", base + "/files/")[0] == 404
