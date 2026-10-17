# Setup on your computer

For AI apps on the same computer: Claude Desktop, Claude Code, Cursor, Codex, VS Code, Windsurf and others. Works on Mac, Windows and Linux.

## 1. Install

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv tool install git+https://github.com/s17sh70x2jfl031ag/Encryptor-MCP
```

Check it:

```bash
encryptor-mcp version
```

## 2. Add it to your AI app

Most apps take this in their MCP settings:

```json
{
  "mcpServers": {
    "encryptor": { "command": "encryptor-mcp", "args": ["stdio"] }
  }
}
```

The exact place for each app is in [connect-your-ai.md](connect-your-ai.md). Claude Desktop also has a one-click [extension](claude-desktop-extension.md).

## 3. Add your vaults

Ask your AI app: **"Open my Encryptor control center."** It opens in your browser, already signed in. Go to **Settings, Add a vault**, give it a name and the vault's folder (the one with `vault.cryptomator` in it). Or create a new vault there.

You can also list vaults in a settings file, `~/.config/encryptor-mcp/.env`:

```
ENCRYPTOR_VAULTS=Taxes=~/Nextcloud/Taxes;Notes=~/Dropbox/Notes
```

All settings are in [.env.example](../.env.example). Whatever you change on the control center wins over the file.

## 4. Use it

Ask your AI about your files. When it needs a vault, a page opens to unlock it. Next time you can also open the control center yourself: it lists your vaults, and unlocking one with its password signs you in.

## Mac extras

- If your AI app can't open the unlock page itself, a native password box appears instead.
- **Show in Finder** on a vault's page shows the open vault as a drive in Finder. Files are decrypted in memory only; deleting there puts things in the vault's trash. It goes away when the vault locks.

## Updating

```bash
uv tool upgrade encryptor-mcp
```

The control center's About page can also check GitHub once a day for a new version (off unless you turn it on).
