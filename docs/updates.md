# Updates

Each release has a version tag (`vX.Y.Z`), notes on the [releases page](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases), and the Claude Desktop extension attached. What changed: [CHANGELOG.md](../CHANGELOG.md).

There's no update command and no ready-made Docker image yet. You update with the tool you installed it with: uv, Git and Docker, or the extension file.

## Know when there's an update

- **On GitHub:** **Watch → Custom → Releases** on the repository. GitHub emails you each new release.
- **Your version:** run `encryptor-mcp version`, or open **About** on the control center. Compare it with the [latest release](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest).
- **Let the control center tell you:** on **About**, tick **Check GitHub for a new version once a day** and press **Save**. Once a day it asks GitHub which release is newest. It sends nothing about you or your vaults. When there's a new one, **About** says so, with a **What's new** link. **Check now** asks right away. Off by default.

## Update by hand

| You run it | To update |
|---|---|
| Claude Desktop extension | Download the newest [`encryptor-mcp.mcpb`](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest/download/encryptor-mcp.mcpb) and open it |
| On your computer (`uv tool`) | `uv tool upgrade encryptor-mcp`, then restart your AI app |
| With `uvx` | Add `--refresh` once to the command, so it fetches the newest code |
| Docker Compose | `git pull`, then `docker compose up -d --build` |
| Without Docker, on a server | `uv tool upgrade encryptor-mcp`, then restart `serve` (for example `sudo systemctl restart encryptor-mcp`) |

If `uv tool upgrade` says there's nothing new, reinstall from GitHub:

```bash
uv tool install --force git+https://github.com/s17sh70x2jfl031ag/Encryptor-MCP
```

Restarting locks every open vault, so unlock again afterwards.

## Update every week by itself (optional)

On a computer, your system can run the update for you. It installs the newest version, or does nothing if you're up to date. Restart your AI app afterwards to use it.

<details>
<summary><b>Mac</b></summary>

Save as `~/Library/LaunchAgents/com.encryptor-mcp.update.plist` (replace `YOU` with your user name):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.encryptor-mcp.update</string>
  <key>ProgramArguments</key>
  <array><string>/Users/YOU/.local/bin/uv</string><string>tool</string><string>upgrade</string><string>encryptor-mcp</string></array>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer></dict>
  <key>StandardOutPath</key><string>/tmp/encryptor-mcp-update.log</string>
  <key>StandardErrorPath</key><string>/tmp/encryptor-mcp-update.log</string>
</dict>
</plist>
```

Turn it on:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.encryptor-mcp.update.plist
```

`which uv` shows where uv is, if it's not in `~/.local/bin`.

</details>

<details>
<summary><b>Linux</b></summary>

Run `crontab -e`, then add:

```
0 9 * * 1 $HOME/.local/bin/uv tool upgrade encryptor-mcp >> $HOME/.cache/encryptor-mcp-update.log 2>&1
```

</details>

<details>
<summary><b>Windows</b></summary>

1. Open **Task Scheduler** from the Start menu and click **Create Basic Task**.
2. Name it "Encryptor MCP update" and choose **Weekly**.
3. Choose **Start a program**. Program: `uv`. Arguments: `tool upgrade encryptor-mcp`.
4. Finish.

</details>

On a server with Docker Compose there's no update script yet. Run the two commands above by hand, after reading the release notes.

## Staying on one version

Install a version tag instead of the newest code:

```bash
uv tool install --force git+https://github.com/s17sh70x2jfl031ag/Encryptor-MCP@v0.1.0
```

With Docker Compose: `git checkout v0.1.0`, then `docker compose up -d --build`. For the extension, keep the `.mcpb` file you have and don't open a newer one.

## Going back

Something wrong after an update? Go back to the version before, the same way:

- `uv tool`: `uv tool install --force git+https://github.com/s17sh70x2jfl031ag/Encryptor-MCP@v0.1.0` (use the version you had).
- Docker Compose: `git checkout v0.1.0`, then `docker compose up -d --build`.
- Extension: open the previous release's `.mcpb` from the [releases page](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases).

Then tell us what went wrong in an [issue](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/issues/new?template=bug_report.yml).

## What an update never touches

- **Your vaults.** They stay where they are, encrypted, and keep working in Cryptomator.
- **The `.encryptor` folder in each vault,** with the changes, earlier versions and the trash.
- **Your settings:** the settings file, the control center's settings, fingerprints and read logs (`~/.config/encryptor-mcp`, or `/data` in Docker).
- **Connected AI apps** on a server. They stay connected.

Vault passwords and keys are never on disk, so there's nothing of them to keep or lose. A restart only locks the open vaults.
