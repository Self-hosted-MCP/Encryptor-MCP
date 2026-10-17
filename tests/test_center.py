# SPDX-License-Identifier: AGPL-3.0-only
"""The control center (a computer and a server), the web version's AI-app login, and what each app may do."""
import asyncio
import re
import shutil

import pytest
from mcp.server.auth.provider import AuthorizationParams
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl
from starlette.testclient import TestClient

from conftest import FIXTURES, official
from encryptor_mcp import server, unlock as U

PW = "test-password-SIV_GCM"
PASS = "a-long-passphrase"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    """Two vaults: GCM (from the settings file) and Spare (added on the page later). Fresh state each test."""
    v1, v2 = tmp_path / "gcm", tmp_path / "spare"
    shutil.copytree(FIXTURES / "vault-SIV_GCM", v1)
    shutil.copytree(FIXTURES / "vault-SIV_CTRMAC", v2)
    monkeypatch.setattr(server, "ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(server, "PAGE_FILE", tmp_path / "state" / "settings.json")
    monkeypatch.setattr(server, "OAUTH_FILE", tmp_path / "state" / "oauth.json")
    monkeypatch.setattr(server, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(server, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(server, "UPDATE_FILE", tmp_path / "state" / "update.json")
    monkeypatch.setenv("ENCRYPTOR_VAULTS", f"GCM={v1}")
    monkeypatch.delenv("ENCRYPTOR_MODES", raising=False)
    monkeypatch.delenv("ENCRYPTOR_IDLE_MINUTES", raising=False)
    for name in ("_manager", "_pages", "_center", "_mounts", "PROVIDER"):
        monkeypatch.setattr(server, name, None)
    monkeypatch.setenv("ENCRYPTOR_FINDER", "off")
    monkeypatch.setenv("BROWSER", "true")   # webbrowser.open runs `true`: opens nothing, succeeds
    yield v1, v2
    if server._manager:
        server._manager.lock_all("test over")


# ---------------------------------------------------------------- on a computer

@pytest.fixture
def local(setup):
    from encryptor_mcp import web
    lp = server.pages()
    client = TestClient(_wsgi(lp.site), base_url=lp.base)
    yield client, lp, setup
    lp.close()


def _wsgi(site):
    """A tiny ASGI wrapper around Site.handle, so the same TestClient drives local and hosted pages."""
    from urllib.parse import parse_qs

    async def app(scope, receive, send):
        body = b""
        while True:
            msg = await receive()
            body += msg.get("body", b"")
            if not msg.get("more_body"):
                break
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        parsed = parse_qs(body.decode(), keep_blank_values=True)
        form = {k: v[0] for k, v in parsed.items()}
        form["vault_list"] = parsed.get("vault", [])
        query = {k: v[0] for k, v in parse_qs(scope.get("query_string", b"").decode()).items()}
        status, extra, out = site.handle(scope["method"], scope["path"], form, headers, query)
        out = out if isinstance(out, bytes) else out.encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(k.lower().encode(), str(v).encode()) for k, v in extra.items()]})
        await send({"type": "http.response.body", "body": out})
    return app


def csrf_of(html):
    return re.search(r'name="csrf" value="([^"]+)"', html)[1]


def test_local_center_needs_the_one_time_link(local):
    client, lp, _ = local
    r = client.get("/")
    assert r.status_code == 200 and "Open your control center" in r.text
    assert "/signin/unlock/GCM" in r.text and "Settings" not in r.text and "Lent to" not in r.text and "Lock" not in r.text.replace("Unlock", "")
    assert client.get("/signin/not-a-code").status_code == 410
    link = lp.signin_url().split(lp.base)[1]
    r = client.get(link, follow_redirects=False)
    assert r.status_code == 303 and "HttpOnly" in r.headers["set-cookie"] and "SameSite=Strict" in r.headers["set-cookie"]
    client.cookies.set("encryptor_center", r.headers["set-cookie"].split(";")[0].split("=", 1)[1])
    assert "GCM" in client.get("/").text
    assert client.get(link).status_code == 410            # the link works once


def signed_in(client, lp):
    r = client.get(lp.signin_url().split(lp.base)[1], follow_redirects=False)
    client.cookies.set("encryptor_center", r.headers["set-cookie"].split(";")[0].split("=", 1)[1])
    return csrf_of(client.get("/").text)


def test_control_center_tool_opens_the_browser_without_telling_the_ai(local):
    client, lp, _ = local
    out = server.control_center()
    assert "Opened the control center" in out and "signin" not in out and lp.base not in out


def test_unlock_and_lock_from_the_center(local):
    client, lp, _ = local
    csrf = signed_in(client, lp)
    assert client.post("/vaults/GCM/unlock", data={}, headers={"origin": lp.base}).status_code == 403   # no csrf
    r = client.post("/vaults/GCM/unlock", data={"csrf": csrf}, headers={"origin": lp.base}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/unlock/")
    page = client.get(r.headers["location"]).text
    assert "Unlock GCM" in page and "Asked by" not in page          # the person asked, not an app
    r = client.post(r.headers["location"], data={"password": PW, "keep": "1h"}, headers={"origin": lp.base},
                    follow_redirects=False)
    assert r.status_code == 303
    home = client.get("/").text
    assert "Due " in home and "You, from the control center" in home
    client.post("/vaults/GCM/lock", data={"csrf": csrf}, headers={"origin": lp.base})
    assert "Locked" in client.get("/").text and server.manager().status("GCM") is None


def test_other_sites_cant_post(local):
    client, lp, _ = local
    csrf = signed_in(client, lp)
    r = client.post("/vaults/GCM/unlock", data={"csrf": csrf}, headers={"origin": "https://evil.example"})
    assert r.status_code == 403


def test_settings_add_mode_remove_idle(local):
    client, lp, (v1, v2) = local
    csrf = signed_in(client, lp)
    o = {"origin": lp.base}
    r = client.post("/settings", data={"csrf": csrf, "kind": "add", "name": "Spare", "path": str(v1.parent / "nope")}, headers=o)
    assert r.status_code == 400 and "no vault.cryptomator" in r.text
    r = client.post("/settings", data={"csrf": csrf, "kind": "add", "name": "Spare", "path": str(v2), "mode": "hidden"}, headers=o)
    assert "Added Spare" in r.text
    assert "Spare" not in server.vaults() and "Spare" in client.get("/").text   # hidden from the AI, not from you
    client.post("/settings", data={"csrf": csrf, "kind": "mode", "name": "Spare", "mode": "read"}, headers=o)
    assert "Spare: locked (read only)" in server.vaults()
    client.post("/settings", data={"csrf": csrf, "kind": "remove", "name": "Spare"}, headers=o)
    assert "Spare" not in server.vaults() and (v2 / "vault.cryptomator").exists()
    client.post("/settings", data={"csrf": csrf, "kind": "idle", "idle": "30"}, headers=o)
    assert server.manager().idle == 30 * 60


def test_setup_file_vaults_are_editable_on_the_page(local, monkeypatch):
    """The setup file only gives starting values; the page changes every vault, and the file is never edited."""
    client, lp, (v1, v2) = local
    monkeypatch.setenv("ENCRYPTOR_MODES", "GCM=read")
    monkeypatch.setenv("ENCRYPTOR_IDLE_MINUTES", "5")
    csrf = signed_in(client, lp)
    o = {"origin": lp.base}
    assert "GCM: locked (read only)" in server.vaults()               # the file's starting value
    client.post("/settings", data={"csrf": csrf, "kind": "mode", "name": "GCM", "mode": "full"}, headers=o)
    assert "GCM: locked\n" in server.vaults() + "\n" and "read only" not in server.vaults()
    client.post("/settings", data={"csrf": csrf, "kind": "idle", "idle": "30"}, headers=o)
    assert server.manager().idle == 30 * 60
    r = client.post("/settings/vault/GCM", data={"csrf": csrf, "kind": "rename", "new_name": "Main", "confirm": "yes"}, headers=o)
    assert "Renamed GCM to Main" in r.text and "Main: locked" in server.vaults()
    r = client.post("/settings/vault/Main", data={"csrf": csrf, "kind": "path", "path": str(v2), "confirm": "yes"}, headers=o)
    assert "points at the new folder" in r.text
    m = server.manager()
    assert m.unlock(m.request_unlock("Main"), "test-password-SIV_CTRMAC")   # now the CTR vault
    r = client.post("/settings/vault/Main", data={"csrf": csrf, "kind": "remove", "confirm": "yes"}, headers=o)
    assert "Removed Main" in r.text and "Your vaults" in r.text and server.vaults().startswith("No vaults yet")
    assert not server.ENV_FILE.exists() or "Main" not in server.ENV_FILE.read_text()


def test_vault_page_record_undo_and_purge(local):
    client, lp, _ = local
    m = server.manager()
    s = m.unlock(m.request_unlock("GCM", "Claude"), PW)
    j = server.journal(s)
    j.write("/new.txt", b"x", "", "Claude", "draft")
    j.trash("/big.bin", "Claude", "tidy")
    base = f"/vault/{s.status_code}"
    page = client.get(base).text
    assert "Record" in page and "Created /new.txt" in page and "Trashed /big.bin" in page and "Restore" in page
    o = {"origin": lp.base}
    r = client.post(base + "/purge", data={"item": ""}, headers=o)
    assert r.status_code == 400 and "Tick the box" in r.text and j.trash_items()
    cid = j.records(1)[0]["id"]
    client.post(base + "/undo", data={"change": cid}, headers=o)              # restore big.bin
    assert s.tree.resolve("/big.bin") and not j.trash_items()
    j.trash("/new.txt", "Claude", "")
    r = client.post(base + "/purge", data={"item": "", "confirm": "yes"}, headers=o)
    assert "Deleted 1 item(s) for good" in r.text and not j.trash_items()
    assert j.records(1)[0]["app"] == "You (control center)"


def test_vault_page_leads_to_the_center_on_a_computer(local):
    client, lp, _ = local
    m = server.manager()
    s = m.unlock(m.request_unlock("GCM"), PW)
    r = client.get(f"/vault/{s.status_code}/center", follow_redirects=False)
    assert r.status_code == 303 and "encryptor_center=" in r.headers["set-cookie"]


# ---------------------------------------------------------------- on a server (the web version)

@pytest.fixture
def hosted(setup, monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("PUBLIC_URL", "http://localhost")
    app = server.build_server(True)
    client = TestClient(app.streamable_http_app(), base_url="http://localhost")
    yield client, server.PROVIDER, setup


def test_hosted_sign_in_and_lockout(hosted):
    client, provider, _ = hosted
    assert "Passphrase" in client.get("/").text
    o = {"origin": "http://localhost"}
    for _ in range(5):
        assert client.post("/signin", data={"passphrase": "wrong-one!"}, headers=o).status_code == 401
    assert client.post("/signin", data={"passphrase": PASS}, headers=o).status_code == 429
    provider.lockout.failures.clear()
    for i in range(5):   # wrong tries from somewhere else don't lock the owner out
        provider.lockout.failed("8.8.8.8")
    assert provider.lockout.locked("8.8.8.8") and not provider.lockout.locked("9.9.9.9")
    provider.lockout.failures.clear()
    for i in range(50):  # but many addresses together still pause everyone
        provider.lockout.failed(f"8.8.4.{i}")
    assert provider.lockout.locked("9.9.9.9")
    provider.lockout.failures.clear()
    r = client.post("/signin", data={"passphrase": PASS}, headers=o, follow_redirects=False)
    assert r.status_code == 303
    assert "Your vaults" in client.get("/").text and "Connected AI apps" in client.get("/").text
    assert client.get("/signin/anything").status_code == 404     # no link sign-in on a server


def connect(provider, cid="c1", name="Phone Claude"):
    info = OAuthClientInformationFull(client_id=cid, client_name=name, redirect_uris=[AnyUrl("https://claude.ai/cb")])
    asyncio.run(provider.register_client(info))
    params = AuthorizationParams(state="s", scopes=["encryptor"], code_challenge="x" * 43,
                                 redirect_uri=AnyUrl("https://claude.ai/cb"), redirect_uri_provided_explicitly=True)
    return asyncio.run(provider.authorize(info, params)).split("req=")[1]


def test_app_login_picks_vaults_and_change(hosted):
    client, provider, _ = hosted
    req = connect(provider)
    page = client.get(f"/login?req={req}").text
    assert "Connect Phone Claude" in page and "GCM" in page
    o = {"origin": "http://localhost"}
    assert client.post("/login", data={"req": req, "passphrase": PASS}, headers=o).status_code == 400   # no vault ticked
    assert client.post("/login", data={"req": req, "passphrase": "nope-nope", "vault": "GCM"}, headers=o).status_code == 401
    r = client.post("/login", data={"req": req, "passphrase": PASS, "vault": ["GCM", "Ghost"]}, headers=o,
                    follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"].startswith("https://claude.ai/cb?code=")
    assert provider.grants["c1"]["vaults"] == ["GCM"] and provider.grants["c1"]["change"] is False


def test_app_sees_only_granted_vaults_and_may_not_change(hosted, monkeypatch):
    client, provider, (v1, v2) = hosted
    monkeypatch.setenv("ENCRYPTOR_VAULTS", f"GCM={v1};Other={v2}")
    server.refresh()
    provider.grants["c1"] = {"vaults": ["GCM"], "change": False}
    monkeypatch.setattr(server, "current_app", lambda: "c1")
    out = server.vaults()
    assert "GCM" in out and "Other" not in out
    with pytest.raises(ToolError, match="No vault called"):
        server.list_folder("Other")
    m = server.manager()
    m.unlock(m.request_unlock("GCM"), PW)
    assert "hello.txt" in server.list_folder("GCM")
    with pytest.raises(ToolError, match="may only read"):
        server.make_folder("GCM", "/x", "t", None)


def test_unlock_link_points_at_the_server(hosted):
    _, _, _ = hosted
    assert server.pages().unlock_url("abc") == "http://localhost/unlock/abc"


def test_tokens_stored_as_fingerprints(hosted):
    _, provider, _ = hosted
    tok = provider.issue("c1", ["encryptor"], None)
    text = server.OAUTH_FILE.read_text()
    assert tok.access_token not in text and tok.refresh_token not in text


def test_serve_refuses_plain_http_on_the_internet(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("PUBLIC_URL", "http://example.com")
    with pytest.raises(SystemExit, match="https"):
        server.serve()


def test_light_by_default_and_a_switch(local):
    client, lp, _ = local
    page = client.get("/").text
    assert "<html lang=\"en\">" in page and 'content="light"' in page and "Switch to dark mode" in page
    r = client.post("/theme", data={"next": "/settings"}, headers={"origin": lp.base}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/settings" and "theme=dark" in r.headers["set-cookie"]
    client.cookies.set("theme", "dark")
    page = client.get("/").text
    assert '<html lang="en" data-theme=dark>' in page and "Switch to light mode" in page
    r = client.post("/theme", data={"next": "//evil.example/x"}, headers={"origin": lp.base}, follow_redirects=False)
    assert r.headers["location"] == "/" and "theme=light" in r.headers["set-cookie"]


def test_per_vault_settings_page(local):
    client, lp, (v1, v2) = local
    csrf = signed_in(client, lp)
    o = {"origin": lp.base}
    home = client.get("/").text
    assert 'href="/settings/vault/GCM"' in home and 'href="/settings#add"' in home
    page = client.get("/settings/vault/GCM").text
    assert "Cryptomator vault format 8, SIV_GCM" in page and "Locked" in page and "Remove from the list" in page
    client.post("/settings", data={"csrf": csrf, "kind": "add", "name": "Spare", "path": str(v2)}, headers=o)
    page = client.get("/settings/vault/Spare").text
    assert "SIV_CTRMAC" in page and "Remove from the list" in page
    r = client.post("/settings/vault/Spare", data={"csrf": csrf, "kind": "mode", "mode": "read"}, headers=o)
    assert "read only" in r.text.lower() and "Spare: locked (read only)" in server.vaults()
    r = client.post("/settings/vault/Spare", data={"csrf": csrf, "kind": "remove"}, headers=o)
    assert "Remove Spare?" in r.text and "Yes, remove it" in r.text and "Spare" in server.vaults()   # asked, not done
    r = client.post("/settings/vault/Spare", data={"csrf": csrf, "kind": "rename", "new_name": "Other"}, headers=o)
    assert "Rename Spare?" in r.text and "Other" not in server.vaults()
    r = client.post("/settings/vault/Spare", data={"csrf": csrf, "kind": "path", "path": str(v1)}, headers=o)
    assert "Change Spare&#x27;s folder?" in r.text or "Change Spare's folder?" in r.text
    r = client.post("/settings/vault/Spare", data={"csrf": csrf, "kind": "remove", "confirm": "yes"}, headers=o)
    assert "Removed Spare" in r.text and "Your vaults" in r.text and "Spare" not in server.vaults()
    assert client.get("/settings/vault/Nope").status_code == 404


# ---------------------------------------------------------------- safety, per-vault options, sign-ins, about

def test_read_only_for_all_and_delete_switch(local):
    client, lp, _ = local
    csrf = signed_in(client, lp)
    o = {"origin": lp.base}
    m = server.manager()
    m.unlock(m.request_unlock("GCM"), PW)
    client.post("/settings", data={"csrf": csrf, "kind": "safety", "read_only_all": "yes", "allow_purge": "yes"}, headers=o)
    assert "READ ONLY FOR EVERY AI APP" in server.vaults() and "Read only for every AI app is on" in client.get("/").text
    with pytest.raises(ToolError, match="Read only for every AI app"):
        server.make_folder("GCM", "/x", "t", None)
    client.post("/settings", data={"csrf": csrf, "kind": "safety"}, headers=o)   # both off
    assert "READ ONLY" not in server.vaults()
    with pytest.raises(ToolError, match="switched off for AI apps"):
        asyncio.run(server.empty_trash("GCM", "t", None))


def test_lock_all_from_the_center(local):
    client, lp, (v1, v2) = local
    csrf = signed_in(client, lp)
    m = server.manager()
    m.unlock(m.request_unlock("GCM"), PW)
    assert "Lock all" in client.get("/").text
    r = client.post("/vaults/lock-all", data={"csrf": csrf}, headers={"origin": lp.base})
    assert "Every vault is locked" in r.text and not m.sessions


def test_rename_move_own_autolock_and_default(local):
    client, lp, (v1, v2) = local
    csrf = signed_in(client, lp)
    o = {"origin": lp.base}
    client.post("/settings", data={"csrf": csrf, "kind": "add", "name": "Spare", "path": str(v2)}, headers=o)
    base = "/settings/vault/Spare"
    r = client.post(base, data={"csrf": csrf, "kind": "vault_idle", "idle": "30"}, headers=o)
    assert "locks after 30 minutes" in r.text
    m = server.manager()
    assert m.idle_for(m.spec("Spare")) == 30 * 60 and m.idle_for(m.spec("GCM")) == 10 * 60
    r = client.post(base, data={"csrf": csrf, "kind": "default", "on": "yes"}, headers=o)
    assert "default vault" in r.text and "Spare: locked  [default" in server.vaults()
    s = m.unlock(m.request_unlock("Spare"), "test-password-SIV_CTRMAC")
    r = client.post(base, data={"csrf": csrf, "kind": "rename", "new_name": "Archive", "confirm": "yes"}, headers=o)
    assert "Renamed Spare to Archive" in r.text and m.status("Archive") is None and set(s.key.enc) == {0}
    assert "Archive: locked  [default" in server.vaults() and m.idle_for(m.spec("Archive")) == 30 * 60
    r = client.post("/settings/vault/Archive", data={"csrf": csrf, "kind": "path", "path": str(v1.parent / "nope"), "confirm": "yes"}, headers=o)
    assert r.status_code == 400 and "no vault.cryptomator" in r.text
    r = client.post("/settings/vault/GCM", data={"csrf": csrf, "kind": "rename", "new_name": "X", "confirm": "yes"}, headers=o)
    assert "Renamed GCM to X" in r.text


def test_devices_and_sign_in_log(hosted):
    client, provider, _ = hosted
    o = {"origin": "http://localhost"}
    client.post("/signin", data={"passphrase": "wrong-wrong"}, headers=o)
    other = TestClient(client.app, base_url="http://localhost")
    other.post("/signin", data={"passphrase": PASS}, headers={**o, "user-agent": "Mozilla/5.0 (iPhone) Safari/605"})
    r = client.post("/signin", data={"passphrase": PASS, "remember": "yes"}, headers=o, follow_redirects=False)
    assert "Max-Age=7776000" in r.headers["set-cookie"]
    page = client.get("/activity").text
    assert "Safari on iPhone" in page and "this browser" in page and "remembered 90 days" in page
    assert "Refused" in page and "Signed in" in page and PASS not in page
    assert "Your AI apps can&#x27;t see this page" in page or "Your AI apps can't see this page" in page
    assert "http://localhost/mcp" in client.get("/settings").text   # the address to give AI apps
    csrf = csrf_of(page)
    client.post("/devices/others/signout", data={"csrf": csrf}, headers=o)
    assert other.get("/").text.count("Passphrase") >= 1        # the other browser is signed out
    assert server._center.sessions.path.exists()                # remembered sign-ins survive a restart
    assert PASS not in server._center.sessions.log_path.read_text()


def test_about_and_update_check(local, monkeypatch):
    client, lp, _ = local
    csrf = signed_in(client, lp)
    page = client.get("/about").text
    assert "AGPL-3.0" in page and "Report a security problem privately" in page and "Not made by or affiliated" in page
    import io, json as _json, urllib.request
    monkeypatch.setattr(server, "current_version", lambda: "0.1.0")
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=5: io.BytesIO(_json.dumps({"tag_name": "v0.2.0", "html_url": "https://x"}).encode()))
    r = client.post("/about", data={"csrf": csrf, "kind": "check_now"}, headers={"origin": lp.base})
    assert "Version 0.2.0 is available" in r.text


def test_read_log_on_the_vault_page_only(local):
    client, lp, _ = local
    m = server.manager()
    s = m.unlock(m.request_unlock("GCM", "Claude"), PW)
    server.read_file("GCM", "/hello.txt", "check the greeting")
    client.get(f"/vault/{s.status_code}/open/hello.txt")
    page = client.get(f"/vault/{s.status_code}").text
    assert "Read log" in page and "Private to you. Your AI apps can" in page
    assert "Read /hello.txt" in page and "check the greeting" in page and "Viewed /hello.txt" in page
    assert "Intact: 2 entries" in page
    tools = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert not any("log" in name for name in tools)                       # no AI tool reads it


def test_sign_in_by_unlocking_a_vault(local, monkeypatch):
    client, lp, (v1, v2) = local
    monkeypatch.setenv("ENCRYPTOR_VAULTS", f"GCM={v1};Secret={v2}")
    monkeypatch.setenv("ENCRYPTOR_MODES", "Secret=hidden")
    server.refresh()
    page = client.get("/").text
    assert "Unlock a vault with its password" in page and "GCM" in page and "Secret" not in page
    o = {"origin": lp.base}
    assert client.post("/signin/unlock/Secret", headers=o).status_code == 404      # hidden stays hidden
    r = client.post("/signin/unlock/GCM", headers=o, follow_redirects=False)
    unlock = r.headers["location"]
    r = client.post(unlock, data={"password": "wrong-one", "keep": "1h"}, headers=o)
    assert r.status_code == 401 and "encryptor_center" not in client.cookies
    r = client.post(client.post("/signin/unlock/GCM", headers=o, follow_redirects=False).headers["location"],
                    data={"password": PW, "keep": "1h"}, headers=o, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/" and "encryptor_center=" in r.headers["set-cookie"]
    client.cookies.set("encryptor_center", r.headers["set-cookie"].split(";")[0].split("=", 1)[1])
    assert "Your vaults" in client.get("/").text and server.manager().status("GCM")
    assert "vault password" in client.get("/activity").text


def test_create_vault_password_and_recovery_on_the_page(local, tmp_path):
    client, lp, _ = local
    csrf = signed_in(client, lp)
    o = {"origin": lp.base}
    where = tmp_path / "Synced"
    where.mkdir()
    form = {"csrf": csrf, "kind": "create", "name": "Private", "where": str(where), "new": "first pass 1",
            "again": "first pass 2"}
    assert "don&#x27;t match" in client.post("/settings", data=form, headers=o).text
    r = client.post("/settings", data={**form, "again": "first pass 1"}, headers=o)
    assert "Recovery key for Private" in r.text and "Private is ready" in r.text
    words = re.findall(r'<li><span class="n">\d+</span>([a-z]+)</li>', r.text)
    assert len(words) == 44 and "Private: locked" in server.vaults()
    assert official("dump", str(where / "Private"), "first pass 1") == []          # Cryptomator opens it
    base = "/settings/vault/Private"
    r = client.post(base, data={"csrf": csrf, "kind": "password", "old": "nope nope", "new": "second pass",
                                "again": "second pass"}, headers=o)
    assert r.status_code == 400 and "Wrong password" in r.text
    r = client.post(base, data={"csrf": csrf, "kind": "password", "old": "first pass 1", "new": "second pass",
                                "again": "second pass"}, headers=o)
    assert "Password changed" in r.text
    r = client.post(base, data={"csrf": csrf, "kind": "show_key", "old": "second pass"}, headers=o)
    assert re.findall(r'<li><span class="n">\d+</span>([a-z]+)</li>', r.text) == words   # same key, same words
    r = client.post(base, data={"csrf": csrf, "kind": "reset", "recovery": " ".join(words), "new": "third pass",
                                "again": "third pass"}, headers=o)
    assert "New password set with the recovery key" in r.text
    m = server.manager()
    assert m.unlock(m.request_unlock("Private"), "third pass")
    tools = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert not tools & {"create_vault", "change_password", "show_recovery_key", "reset_password"}   # never via the AI


def test_change_a_connected_apps_vaults(hosted, monkeypatch):
    client, provider, (v1, v2) = hosted
    monkeypatch.setenv("ENCRYPTOR_VAULTS", f"GCM={v1};Other={v2}")
    server.refresh()
    o = {"origin": "http://localhost"}
    client.post("/signin", data={"passphrase": PASS}, headers=o)
    provider.clients["c1"] = OAuthClientInformationFull(client_id="c1", client_name="Phone Claude",
                                                         redirect_uris=[AnyUrl("https://claude.ai/cb")])
    provider.grants["c1"] = {"vaults": ["GCM"], "change": False}
    home = client.get("/").text
    assert "Phone Claude" in home and 'href="/apps/c1"' in home
    page = client.get("/apps/c1").text
    csrf = csrf_of(page)
    r = client.post("/apps/c1", data={"csrf": csrf, "vault": ["GCM", "Other", "Ghost"], "change": "yes"}, headers=o)
    assert "Saved" in r.text and provider.grants["c1"]["vaults"] == ["GCM", "Other"] and provider.grants["c1"]["change"]
    monkeypatch.setattr(server, "current_app", lambda: "c1")
    assert "Other" in server.vaults()


def test_an_app_cant_pose_as_the_person(local):
    """Only the sign-in page's own unlock signs in or skips the warning; an app's name decides nothing."""
    from encryptor_mcp.auth import app_label
    from encryptor_mcp.web import SIGNIN_APP
    assert app_label("You, signing in") == "An AI app called You, signing in" and app_label("Claude") == "Claude"
    client, lp, _ = local
    m = server.manager()
    code = m.request_unlock("GCM", SIGNIN_APP, "")          # an app that managed to use the exact name
    page = client.get(f"/unlock/{code}").text
    assert "Only continue if you asked your AI app" in page
    r = client.post(f"/unlock/{code}", data={"password": PW, "keep": "1h"}, headers={"origin": lp.base},
                    follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/vault/") and "set-cookie" not in r.headers


def test_client_address_behind_the_proxy():
    ip = server.client_ip
    assert ip("172.18.0.3", "6.6.6.6, 9.9.9.9") == "9.9.9.9"   # Caddy appends the real one last
    assert ip("8.8.8.8", "9.9.9.9") == "8.8.8.8"               # straight from the internet: ignored
    assert ip("127.0.0.1", "") == "127.0.0.1"


def test_server_request_lines_hide_secret_addresses():
    import logging
    rec = logging.LogRecord("uvicorn.access", 20, "", 0, '%s - "%s %s HTTP/%s" %d',
                            ("1.2.3.4:5", "GET", "/vault/SeCrEt123/open/a.txt?x=1", "1.1", 200), None)
    server.redact_access_line(rec)
    assert rec.args[2] == "/vault/<hidden>/open/a.txt" and "SeCrEt" not in rec.getMessage()
    for path, shown in (("/unlock/abc", "/unlock/<hidden>"), ("/signin/xyz", "/signin/<hidden>"),
                        ("/login?req=r&code=c", "/login"), ("/mcp", "/mcp")):
        rec.args = ("a", "GET", path, "1.1", 200)
        server.redact_access_line(rec)
        assert rec.args[2] == shown


def test_server_pages_answer_only_their_own_address(hosted):
    client, _, _ = hosted
    assert client.get("/", headers={"host": "evil.example"}).status_code == 421
    assert client.get("/signin", headers={"host": "localhost"}).status_code == 200
