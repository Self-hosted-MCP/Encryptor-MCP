# Updates

Each release has a version tag (`vX.Y.Z`), notes on the [releases page](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases), a ready-made Docker image, and the Claude Desktop extension attached. What changed: [CHANGELOG.md](../CHANGELOG.md).

The update command, the update script and the ready-made image only ever install a published release. A few ways follow the newest code instead (the `main` branch): Railway's one-click template, `uvx` with `--refresh`, and `git pull`. They're marked below.

## Know when there's an update

- **On GitHub:** **Watch → Custom → Releases** on the repository. GitHub emails you each new release.
- **Your version:** run `encryptor-mcp version`, or open **About** on the control center. Compare it with the [latest release](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest).
- **Let the control center tell you:** on **About**, tick **Check GitHub for a new version once a day** and press **Save**. Once a day it asks GitHub which release is newest. It sends nothing about you or your vaults. When there's a new one, **About** says so, with a **What's new** link. **Check now** asks right away. Off by default.

## Update by hand

| You run it | To update |
|---|---|
| Claude Desktop extension | Download the newest [`encryptor-mcp.mcpb`](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest/download/encryptor-mcp.mcpb) and open it |
| On your computer (`uv tool`) | `encryptor-mcp update` (installs the newest release, or says you're up to date), then restart your AI app |
| Claude Code plugin | `claude plugin marketplace update encryptor`, then restart Claude Code |
| With `uvx` | Add `--refresh` once to the command, so it fetches the newest code (`main`) |
| Docker Compose, built here | `./scripts/update.sh` (moves to the newest release and restarts). Or, for the newest code: `git checkout main`, `git pull`, then `docker compose up -d --build` |
| Docker, ready-made image | `docker pull ghcr.io/s17sh70x2jfl031ag/encryptor-mcp:latest`, then start the container again (same `/data` volume) |
| Railway | **Redeploy** the service (the one-click template builds the newest code, `main`) |
| Render | **Manual Deploy** (it pulls `:latest` again) |
| Without Docker, on a server | `encryptor-mcp update`, then restart `serve` (for example `sudo systemctl restart encryptor-mcp`) |

Restarting locks every open vault, so unlock again afterwards.

## Update every week by itself (optional)

On a computer, your system can run `encryptor-mcp update` for you. It installs the newest release, or does nothing if you're up to date. Restart your AI app afterwards to use it.

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
  <array><string>/Users/YOU/.local/bin/encryptor-mcp</string><string>update</string></array>
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

`which encryptor-mcp` shows where it is, if it's not in `~/.local/bin`.

</details>

<details>
<summary><b>Linux</b></summary>

Run `crontab -e`, then add:

```
0 9 * * 1 $HOME/.local/bin/encryptor-mcp update >> $HOME/.cache/encryptor-mcp-update.log 2>&1
```

</details>

<details>
<summary><b>Windows</b></summary>

1. Open **Task Scheduler** from the Start menu and click **Create Basic Task**.
2. Name it "Encryptor MCP update" and choose **Weekly**.
3. Choose **Start a program**. Program: `encryptor-mcp`. Arguments: `update`.
4. Finish.

</details>

### On your own server (Docker Compose)

[`scripts/update.sh`](../scripts/update.sh) moves your copy to the newest official release and restarts it, only if there's a new one. It refuses to run if you changed files in your copy. Run it by hand, or every week with cron (`crontab -e`):

```
0 4 * * 1 cd /path/to/Encryptor-MCP && ./scripts/update.sh >> update.log 2>&1
```

### Your own fork on a hosting company

If Railway builds from your fork of this repository, the fork can follow official releases by itself: in your fork, turn on Actions, then add the repository variable `AUTO_UPDATE` = `on` (**Settings → Secrets and variables → Actions → Variables**). Every Monday, [the workflow](../.github/workflows/update-from-releases.yml) merges the newest release into your fork, and your host rebuilds. It never runs in the original repository, and it stops without changing anything if the release conflicts with your own changes. GitHub doesn't let it change workflow files, so when a release changes one, update your fork by hand: **Sync fork** on GitHub.

## Keeping Python up to date

Encryptor runs on Python, the language it's written in. Updating Encryptor doesn't update Python, and that's fine: Encryptor works on Python 3.11 and newer, and its tests run on 3.11 and 3.14 for every change.

- **Docker, Railway, Render:** nothing to do. Python comes inside the image, and each Encryptor release is built on the newest Python 3.14.
- **On your computer, installed with uv:** uv chose a Python when you installed Encryptor. Now and then (for example every few months), get its newest fixes:

  ```bash
  uv python upgrade
  ```

  This installs the newest patch of each Python uv manages (like 3.14.1 to 3.14.2), and Encryptor uses it from then on. Restart your AI app afterwards. If uv uses a Python you installed yourself (from Homebrew or python.org), update that one the way you installed it.

- **Moving to a new Python version** (like 3.14 to 3.15), once Encryptor supports it:

  ```bash
  uv tool upgrade encryptor-mcp --python 3.15
  ```

`encryptor-mcp version` shows Encryptor's version. `uv python list --only-installed` shows the Pythons uv keeps for you.

## Staying on one version

Install a version tag instead of the newest release:

```bash
uv tool install --force git+https://github.com/s17sh70x2jfl031ag/Encryptor-MCP@v0.1.0
```

With Docker Compose: `git checkout v0.1.0`, then `docker compose up -d --build`. With the ready-made image, use the tag `:0.1.0` (exact) or `:0.1` (the newest 0.1.x) instead of `:latest`. For the extension, keep the `.mcpb` file you have and don't open a newer one.

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
