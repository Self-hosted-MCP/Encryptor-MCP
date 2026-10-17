# SPDX-License-Identifier: AGPL-3.0-only
"""The terminal commands (setup, check, update) and the files that install or host it (plugin, Railway, Render)."""
import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import FIXTURES

ROOT = Path(__file__).resolve().parent.parent


def run(tmp_path, *args, stdin="", **env):
    full = {**os.environ, "ENCRYPTOR_CONFIG_DIR": str(tmp_path / "cfg"), "ENCRYPTOR_VAULTS": "", **env}
    return subprocess.run([sys.executable, "-m", "encryptor_mcp", *args], input=stdin, capture_output=True,
                          text=True, env=full, timeout=60)


def test_check_reports_each_vault_without_opening_it(tmp_path):
    r = run(tmp_path, "check", ENCRYPTOR_VAULTS=f"GCM={FIXTURES / 'vault-SIV_GCM'};Gone={tmp_path / 'nope'}")
    assert r.returncode == 1
    assert "GCM:" in r.stdout and "ok (format 8, SIV_GCM)" in r.stdout
    assert "Gone:" in r.stdout and "folder not found" in r.stdout and "1 problem(s) found" in r.stderr
    r = run(tmp_path, "check", ENCRYPTOR_VAULTS=f"GCM={FIXTURES / 'vault-SIV_GCM'}")
    assert r.returncode == 0 and "No vault was opened" in r.stdout


def test_check_on_a_server(tmp_path):
    r = run(tmp_path, "check", LOGIN_PASSPHRASE="a-test-passphrase", PUBLIC_URL="https://vault.example.com",
            ENCRYPTOR_VAULTS=f"GCM={FIXTURES / 'vault-SIV_GCM'}")
    assert r.returncode == 0, r.stderr
    assert "Server version: passphrase set; address https://vault.example.com" in r.stdout
    r = run(tmp_path, "check", LOGIN_PASSPHRASE="a-test-passphrase", PUBLIC_URL="http://vault.example.com")
    assert "(must start with https://)" in r.stdout


def test_setup_adds_vaults_and_refuses_wrong_folders(tmp_path):
    answers = f"Mine\n{FIXTURES / 'vault-SIV_CTRMAC'}\nn\nBad\n{tmp_path}\n\n\n"
    r = run(tmp_path, "setup", stdin=answers)
    assert r.returncode == 0 and "Added Mine." in r.stdout and "Not added: That folder has no vault.cryptomator" in r.stdout
    assert "claude mcp add" in r.stdout and "password" not in r.stdout.lower().replace("no password", "")
    r = run(tmp_path, "check")
    assert "Mine:" in r.stdout and "[Read only]" in r.stdout and "Bad" not in r.stdout


def test_help_lists_every_command(tmp_path):
    out = run(tmp_path, "help").stdout
    for cmd in ("stdio", "serve", "setup", "check", "update", "translate", "set-passphrase", "version"):
        assert f"    {cmd} " in out


def test_install_and_hosting_files():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    version = next(l.split('"')[1] for l in (ROOT / "pyproject.toml").read_text().splitlines()
                   if l.startswith("version"))
    assert plugin["version"] == version
    assert f"Encryptor-MCP@v{version}" in " ".join(plugin["mcpServers"]["encryptor"]["args"])   # a release, never main
    assert market["plugins"][0]["name"] == plugin["name"]
    railway = json.loads((ROOT / "railway.json").read_text())
    assert railway["deploy"]["healthcheckPath"] == "/health"
    render = (ROOT / "render.yaml").read_text()
    assert "mountPath: /data" in render and "LOGIN_PASSPHRASE" in render and "encryptor-mcp:latest" in render
    entry = (ROOT / "docker-entrypoint.sh").read_text()
    assert "setpriv --reuid=10001" in entry and 'ENTRYPOINT ["docker-entrypoint.sh"]' in (ROOT / "Dockerfile").read_text()
