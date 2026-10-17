# SPDX-License-Identifier: AGPL-3.0-only
"""The whole flow through a real MCP connection (stdio): unlock via URL mode or a link, read, lock."""
import asyncio
import os
import sys
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import mcp_types as types
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from conftest import FIXTURES


def post_password(url: str, password: str, keep: str = "lock", read_only: bool = False, delay: float = 0.3):
    """Plays the person: opens the unlock page and types the password, a moment later."""
    def go():
        import time
        time.sleep(delay)
        base = url.split("/unlock/")[0]
        data = urlencode({"password": password, "keep": keep, **({"read_only": "yes"} if read_only else {})}).encode()
        req = urllib.request.Request(url, data=data, headers={"Origin": base})
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass
    threading.Thread(target=go, daemon=True).start()


def run(tmp_path, steps, unlock_way="auto", with_elicitation=True, password_for=None):
    env = {**os.environ, "ENCRYPTOR_CONFIG_DIR": str(tmp_path), "ENCRYPTOR_UNLOCK": unlock_way,
           "ENCRYPTOR_VAULTS": f"GCM={FIXTURES / 'vault-SIV_GCM'};CTR={FIXTURES / 'vault-SIV_CTRMAC'};Secret={FIXTURES / 'vault-SIV_GCM'}",
           "ENCRYPTOR_MODES": "CTR=read,Secret=hidden"}
    seen = {}

    async def elicit(ctx, params):
        seen["mode"], seen["url"] = params.mode, getattr(params, "url", None)
        post_password(seen["url"], password_for or "")
        return types.ElicitResult(action="accept")

    async def main():
        params = StdioServerParameters(command=sys.executable, args=["-m", "encryptor_mcp", "stdio"], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w, elicitation_callback=elicit if with_elicitation else None) as s:
                await s.initialize()
                return await steps(s, seen)
    return asyncio.run(asyncio.wait_for(main(), 120))


def text(res):
    return res.content[0].text


def test_url_mode_unlock_read_lock(tmp_path):
    async def steps(s, seen):
        out = {"vaults": text(await s.call_tool("vaults", {}))}
        out["locked_read"] = await s.call_tool("read_file", {"vault": "GCM", "path": "hello.txt", "purpose": "test"})
        out["unlock"] = text(await s.call_tool("unlock", {"vault": "GCM", "purpose": "read the hello file"}))
        out["vaults2"] = text(await s.call_tool("vaults", {}))
        out["list"] = text(await s.call_tool("list_folder", {"vault": "GCM"}))
        out["read"] = text(await s.call_tool("read_file", {"vault": "GCM", "path": "Folder A/Sub folder/notes ü é 日本.txt", "purpose": "test"}))
        out["find"] = text(await s.call_tool("find", {"vault": "GCM", "name_contains": "LONG"}))
        out["info"] = text(await s.call_tool("file_info", {"vault": "GCM", "path": "big.bin"}))
        out["lock"] = text(await s.call_tool("lock", {"vault": "GCM"}))
        out["after_lock"] = await s.call_tool("read_file", {"vault": "GCM", "path": "hello.txt", "purpose": "test"})
        out["seen"] = dict(seen)
        return out
    out = run(tmp_path, steps, password_for="test-password-SIV_GCM")
    assert "GCM: locked" in out["vaults"] and "CTR: locked (read only)" in out["vaults"] and "Secret" not in out["vaults"]
    assert out["locked_read"].is_error and "is locked" in text(out["locked_read"])
    assert out["seen"]["mode"] == "url" and out["seen"]["url"].startswith("http://127.0.0.1:")
    assert out["unlock"].startswith("GCM is open.")
    assert "GCM: OPEN" in out["vaults2"] and "SIV_GCM" in out["vaults2"]
    assert "[folder] Folder A/" in out["list"] and "[link]   link to hello -> hello.txt" in out["list"]
    assert out["read"].startswith("[version ") and out["read"].endswith("]\nUnicode name and text: ü é 日本\n")
    assert "Long folder name" in out["find"] and "a very long file name" in out["find"]
    assert "Size: 97.7 KB" in out["info"] and "Stored encrypted as: d/" in out["info"]
    assert out["lock"] == "GCM is locked." and out["after_lock"].is_error


def test_link_mode_for_apps_without_url_mode(tmp_path):
    async def steps(s, seen):
        res = text(await s.call_tool("unlock", {"vault": "CTR", "purpose": "read notes"}))
        url = res.split(": ", 1)[1].split("\n")[0]
        post_password(url, "test-password-SIV_CTRMAC", delay=0)
        await asyncio.sleep(1.5)
        return res, text(await s.call_tool("vaults", {})), \
            text(await s.call_tool("read_file", {"vault": "CTR", "path": "hello.txt", "purpose": "t"}))
    res, status, hello = run(tmp_path, steps, unlock_way="link", with_elicitation=False)
    assert "It works once, for 5 minutes" in res and "never in this chat" in res
    assert "CTR: OPEN (read only)" in status and "SIV_CTRMAC" in status
    assert hello == "Hello from Cryptomator's own code.\n"


def test_hidden_vault_cant_be_unlocked(tmp_path):
    async def steps(s, seen):
        return await s.call_tool("unlock", {"vault": "Secret", "purpose": "x"})
    res = run(tmp_path, steps, unlock_way="link", with_elicitation=False)
    assert res.is_error and "No vault called" in text(res)


def test_unlock_falls_back_when_the_app_cant_open_the_page(tmp_path):
    """Some apps say they can open pages, then fail to: the user still gets the link instead of an error."""
    env = {**os.environ, "ENCRYPTOR_CONFIG_DIR": str(tmp_path), "ENCRYPTOR_UNLOCK": "page",
           "ENCRYPTOR_VAULTS": f"GCM={FIXTURES / 'vault-SIV_GCM'}"}

    async def broken(ctx, params):
        raise RuntimeError("this transport context has no back-channel for server-initiated requests")

    async def main():
        params = StdioServerParameters(command=sys.executable, args=["-m", "encryptor_mcp", "stdio"], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w, elicitation_callback=broken) as s:
                await s.initialize()
                res = await s.call_tool("unlock", {"vault": "GCM", "purpose": "t"})
                url = text(res).split(": ", 1)[1].split("\n")[0]
                post_password(url, "test-password-SIV_GCM", delay=0)
                await asyncio.sleep(1.5)
                return res, text(await s.call_tool("vaults", {}))
    res, status = asyncio.run(asyncio.wait_for(main(), 120))
    assert not res.is_error and "/unlock/" in text(res)
    assert "GCM: OPEN" in status
