# Claude Desktop extension

The quickest way on Claude Desktop: one file, no terminal and no settings file. Claude Desktop runs it on your computer, for Claude Desktop only.

Works with Cryptomator vaults. Not made by or affiliated with Cryptomator.

## What you need

- [Claude Desktop](https://claude.ai/download) on Mac, Windows or Linux, recent enough to install extensions (**Settings → Extensions**).
- One or more Cryptomator vaults on this computer (or in a synced folder it can reach).

You don't need a password to install it. Vault passwords are typed only on the unlock page, never in the extension's settings and never in the chat.

## Install

1. Download [`encryptor-mcp.mcpb`](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest/download/encryptor-mcp.mcpb) from the latest release.
2. Open it (double-click), or in Claude Desktop go to **Settings → Extensions** and drag it in.
3. Claude Desktop shows what it is and asks for two optional settings:

   | Field | What to put |
   |---|---|
   | **Vaults (optional)** | `Name=/path/to/vault;Other=/path/to/other`. Leave it empty to add vaults on the control center instead |
   | **Lock after minutes without use** | An open vault locks by itself after this long. 10 by default |

4. Click **Install**, and make sure the extension is turned on.
5. Start a new chat and ask: *"Open the Encryptor control center."*

The first start takes a little longer: Claude Desktop sets up the program and its packages once.

## Add your vaults

Ask Claude to open the control center. It opens in your own browser, on this computer. Add each vault there: a name and the vault's folder (the one with `vault.cryptomator` in it). There you also choose what Claude may do with each vault (everything, read only, or hidden) and how soon it locks.

Vaults in the **Vaults** field of the extension show up there too.

## The first unlock

Ask something like *"What's in my Taxes vault?"*. The vault is locked, so Claude asks to unlock it:

1. A page opens in your browser. It says which vault and why Claude wants it.
2. You type the vault password there, and choose how long the vault stays open.
3. Claude carries on.

On a Mac, if the page can't open, a native password box shows instead. Either way the password stays on your computer: Claude never sees it, and it never goes through the chat. The keys are kept only in memory, and are wiped when the vault locks or Claude Desktop closes.

## What you get

All 23 tools: list, read, find, write, move, copy, trash, and Cryptomator's health check. Every change is logged and keeps what it replaced. Ask *"what did you change today?"* or *"undo that"*. Deleting for good only happens when you empty the trash, and you approve that yourself, outside the chat.

## Change the settings

**Settings → Extensions → Encryptor MCP → Configure**: change the vaults or the minutes, then restart the extension. Most things are easier on the control center.

## Where things are kept

Your vaults stay where they are, encrypted as before, and keep working in Cryptomator. The change log, earlier versions and the control center's settings are in `~/.config/encryptor-mcp/state`. Passwords and keys are never written to disk.

## Update

Download the newest `.mcpb` and open it again. Your vaults, settings and change log stay.

## Remove

**Settings → Extensions**, then remove **Encryptor MCP**. To remove everything, also delete `~/.config/encryptor-mcp`. Your vaults are not touched.

## If it doesn't work

- **The tools don't appear:** check the extension is turned on, then start a new chat. Restart Claude Desktop if needed.
- **No vaults:** open the control center and add one, or fill in **Vaults** under **Configure**.
- **The unlock page doesn't open:** ask Claude to unlock again. On a Mac a password box shows instead.
- **Nothing happens, or an error about uv or Python:** Claude Desktop sets these up itself; make sure it's up to date, and that your computer can reach the internet for the first start.

## How it's built

The `.mcpb` file is a zip of this project plus [`extension/manifest.json`](../extension/manifest.json). Claude Desktop runs it with uv, from the exact package versions in `uv.lock`, with the command `encryptor-mcp stdio`. To build it yourself: `python3 scripts/build_mcpb.py` (the file lands in `dist/`).
