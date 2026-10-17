# SPDX-License-Identifier: AGPL-3.0-only
"""The leak test: the vault password and the vault's keys never appear in any tool answer, in the server's output,
or in any file Encryptor keeps (settings, sign-ins, logs, fingerprints, change records), in any usual encoding."""
import asyncio
import base64
import os
import re
import shutil
import sys

import mcp_types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from conftest import FIXTURES, password
from test_mcp import post_password
from encryptor_mcp.vault import keys

PW = password("SIV_GCM")


def forms(secret: bytes) -> list[bytes]:
    """The ways a secret could show up in text."""
    out = [secret, secret.hex().encode(), secret.hex().upper().encode(), base64.b64encode(secret),
           base64.urlsafe_b64encode(secret), base64.b64encode(secret).rstrip(b"="),
           base64.urlsafe_b64encode(secret).rstrip(b"=")]
    return [f for f in out if len(f) >= 8]


def test_no_secret_ever_leaves(tmp_path):
    vault = tmp_path / "v"
    shutil.copytree(FIXTURES / "vault-SIV_GCM", vault)
    key = keys.unlock_masterkey((vault / "masterkey.cryptomator").read_bytes(), PW)
    secrets_ = forms(PW.encode()) + forms(key.enc) + forms(key.mac) + forms(key.raw)
    cfg = tmp_path / "cfg"
    env = {**os.environ, "ENCRYPTOR_CONFIG_DIR": str(cfg), "ENCRYPTOR_UNLOCK": "page", "ENCRYPTOR_APPROVE": "code",
           "ENCRYPTOR_VAULTS": f"V={vault}", "ENCRYPTOR_FINDER": "off", "BROWSER": "true"}
    answers = []

    async def elicit(ctx, params):
        if params.mode == "url":
            post_password(params.url, "a wrong password first")       # a wrong try must not leak either
            post_password(params.url, PW, delay=1.6)
            return types.ElicitResult(action="accept")
        return types.ElicitResult(action="decline")

    async def main():
        errlog = open(tmp_path / "stderr.txt", "w")
        params = StdioServerParameters(command=sys.executable, args=["-m", "encryptor_mcp", "stdio"], env=env)
        async with stdio_client(params, errlog=errlog) as (r, w):
            async with ClientSession(r, w, elicitation_callback=elicit) as s:
                await s.initialize()

                async def call(tool, **kw):
                    res = await s.call_tool(tool, kw)
                    answers.append(" ".join(getattr(c, "text", "") for c in res.content))
                    return answers[-1]
                await call("vaults")
                await call("unlock", vault="V", purpose="leak test")
                await call("list_folder", vault="V")
                text = await call("read_file", vault="V", path="hello.txt", purpose="t")
                version = re.search(r"\[version (\w+)", text).group(1)
                await call("write_file", vault="V", path="hello.txt", content="changed", purpose="t", version=version)
                await call("write_file", vault="V", path="new.txt", content="x", purpose="t")
                await call("undo", vault="V", purpose="t")
                await call("trash", vault="V", path="big.bin", purpose="t")
                await call("empty_trash", vault="V", purpose="t")
                await call("health_check", vault="V")
                await call("locate", vault="V", path="hello.txt")
                await call("file_info", vault="V", path="hello.txt")
                await call("recent_changes", vault="V")
                await call("control_center")
                await call("lock")
        errlog.close()
    asyncio.run(asyncio.wait_for(main(), 120))
    assert "is open" in answers[1] or "already open" in answers[1]

    haystacks = {"tool answers": "\n".join(answers).encode(), "server output": (tmp_path / "stderr.txt").read_bytes()}
    for f in cfg.rglob("*"):
        if f.is_file():
            haystacks[str(f.relative_to(cfg))] = f.read_bytes()
    assert any("readlogs" in k for k in haystacks) and any("fingerprints" in k for k in haystacks)
    for where, data in haystacks.items():
        for s in secrets_:
            assert s not in data, f"a secret showed up in {where}"
