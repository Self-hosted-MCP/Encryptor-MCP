# SPDX-License-Identifier: AGPL-3.0-only
"""Changing a vault through a real MCP connection: write, version checks, undo, the trash, and approvals."""
import asyncio
import os
import re
import shutil
import sys

import mcp_types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from conftest import FIXTURES, official, open_tree, password
from test_mcp import post_password, text
from test_vault import ours


def run(tmp_path, steps, approve="ask", answer=True, modes=""):
    vault = tmp_path / "v"
    shutil.copytree(FIXTURES / "vault-SIV_GCM", vault)
    env = {**os.environ, "ENCRYPTOR_CONFIG_DIR": str(tmp_path / "cfg"), "ENCRYPTOR_UNLOCK": "page",
           "ENCRYPTOR_APPROVE": approve, "ENCRYPTOR_VAULTS": f"V={vault}", "ENCRYPTOR_MODES": modes}
    asked = []

    async def elicit(ctx, params):
        if params.mode == "url":
            post_password(params.url, password("SIV_GCM"), read_only=False)
            return types.ElicitResult(action="accept")
        asked.append(params.message)
        return types.ElicitResult(action="accept", content={"allow": answer})

    async def main():
        params = StdioServerParameters(command=sys.executable, args=["-m", "encryptor_mcp", "stdio"], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w, elicitation_callback=elicit) as s:
                await s.initialize()
                async def call(tool, **kw):
                    return await s.call_tool(tool, kw)
                await call("unlock", vault="V", purpose="test")
                return await steps(call, s)
    out = asyncio.run(asyncio.wait_for(main(), 180))
    return out, asked, vault


def test_write_undo_and_trash(tmp_path):
    async def steps(call, s):
        o = {}
        o["new"] = text(await call("write_file", vault="V", path="Notes/today.md", content="x", purpose="t"))
        await call("make_folder", vault="V", path="Notes", purpose="t")
        o["new"] = text(await call("write_file", vault="V", path="Notes/today.md", content="first", purpose="draft"))
        o["blind"] = await call("write_file", vault="V", path="Notes/today.md", content="second", purpose="t")
        read = text(await call("read_file", vault="V", path="Notes/today.md", purpose="t"))
        version = re.search(r"\[version (\w+)", read).group(1)
        o["replace"] = text(await call("write_file", vault="V", path="Notes/today.md", content="second",
                                       purpose="t", version=version))
        o["append"] = text(await call("append_file", vault="V", path="Notes/today.md", content="+", purpose="t"))
        o["versions"] = text(await call("versions", vault="V", path="Notes/today.md"))
        o["undo"] = text(await call("undo", vault="V", purpose="t"))
        o["after_undo"] = text(await call("read_file", vault="V", path="Notes/today.md", purpose="t"))
        o["trash"] = text(await call("trash", vault="V", path="Folder A", purpose="tidy"))
        o["list"] = text(await call("list_folder", vault="V"))
        o["trash_list"] = text(await call("trash_list", vault="V"))
        o["meta"] = await call("read_file", vault="V", path=".encryptor/changes", purpose="peek")
        o["changes"] = text(await call("recent_changes", vault="V"))
        o["empty"] = text(await call("empty_trash", vault="V", purpose="clean up"))
        o["trash_after"] = text(await call("trash_list", vault="V"))
        return o
    o, asked, vault = run(tmp_path, steps)
    assert o["new"].startswith("Created /Notes/today.md")
    assert o["blind"].is_error and "Read it first" in text(o["blind"])
    assert o["replace"].startswith("Replaced") and o["append"].startswith("Added")
    assert o["versions"].count("from before") == 2
    assert o["undo"].startswith("Undone") and o["after_undo"].endswith("\nsecond")
    assert "Folder A" not in o["list"] and ".encryptor" not in o["list"] and "/Folder A/" in o["trash_list"]
    assert o["meta"].is_error and "own records" in text(o["meta"])
    assert "trash /Folder A" in o["changes"] and "(undone)" in o["changes"] and "tidy" in o["changes"]
    assert len(asked) == 1 and "for good" in asked[0] and o["empty"].startswith("Deleted 1")
    assert o["trash_after"] == "The trash is empty."
    assert ours(open_tree(vault, "SIV_GCM")) == official("dump", str(vault), password("SIV_GCM"))


def test_saying_no_keeps_everything(tmp_path):
    async def steps(call, s):
        await call("trash", vault="V", path="big.bin", purpose="t")
        return {"empty": text(await call("empty_trash", vault="V", purpose="t")),
                "left": text(await call("trash_list", vault="V"))}
    o, asked, _ = run(tmp_path, steps, answer=False)
    assert "didn't allow" in o["empty"] and "/big.bin" in o["left"]


def test_code_fallback_needs_the_same_action(tmp_path):
    async def steps(call, s):
        await call("trash", vault="V", path="big.bin", purpose="t")
        first = text(await call("empty_trash", vault="V", purpose="t"))
        code = re.search(r'confirm="(\w+)"', first).group(1)
        item = text(await call("trash_list", vault="V")).split()[0]
        other = text(await call("empty_trash", vault="V", purpose="t", item=item, confirm=code))
        first2 = text(await call("empty_trash", vault="V", purpose="t"))
        code2 = re.search(r'confirm="(\w+)"', first2).group(1)
        done = text(await call("empty_trash", vault="V", purpose="t", confirm=code2))
        again = text(await call("empty_trash", vault="V", purpose="t", confirm=code2))
        return first, other, done, again
    (first, other, done, again), asked, _ = run(tmp_path, steps, approve="code")
    assert "Only if they clearly say yes" in first and not asked
    assert "doesn't match" in other and done.startswith("Deleted 1") and again == "The trash is empty."


def test_read_only_setup_has_no_write_tools(tmp_path):
    async def steps(call, s):
        return sorted(t.name for t in (await s.list_tools()).tools)
    names, *_ = run(tmp_path, steps, modes="V=read")
    assert "write_file" not in names and "empty_trash" not in names and "read_file" in names and "versions" in names
