# Claude Desktop extension

The quickest way on Claude Desktop: one file, no terminal and no settings file. Claude Desktop runs it on your computer, for Claude Desktop only. For other apps see [setup-computer.md](setup-computer.md). For your phone, add a free tunnel on this computer ([Use it from your phone](setup-computer.md#use-it-from-your-phone)), or use [your own server](setup-own-server.md).

Works with Cryptomator vaults. Not made by or affiliated with Cryptomator.

## What you need

- [Claude Desktop](https://claude.ai/download) on Mac, Windows or Linux, recent enough to install extensions (**Settings → Extensions**).
- One or more Cryptomator vaults on this computer, or in a synced folder it can reach ([where-your-vaults-live.md](where-your-vaults-live.md)). No vault yet? You can create one on the control center.
- An internet connection for the first start.

You don't need a password to install it. Vault passwords are typed only on the unlock page, never in the extension's settings and never in the chat.

## Install

1. Download [`encryptor-mcp.mcpb`](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest/download/encryptor-mcp.mcpb) from the latest release.
2. Open it (double-click), or in Claude Desktop go to **Settings → Extensions** and drag it in.
3. Claude Desktop shows what it is and asks for two optional settings:

   | Field | What to put |
   |---|---|
   | **Vaults (optional)** | A vault folder, like `~/Nextcloud/Taxes`, or several separated by `;`. To give one another name: `Taxes 2025=~/Nextcloud/Taxes`. Leave it empty to add vaults on the control center instead |
   | **Lock after minutes without use** | An open vault locks by itself after this long. 10 by default |

4. Click **Install**, and make sure the extension is turned on.
5. Start a new chat and ask: *"Open my Encryptor control center."*

The first start takes a little longer: Claude Desktop sets up the program and its packages once.

## Add your vaults

The control center opens in your own browser, on this computer, already signed in. Go to **Settings**. Under **Add a vault**, type a **Name** and the **Vault folder** (the one with `vault.cryptomator` in it), choose what **The AI may** do, and press **Add vault**. There you also choose how soon vaults lock.

Vaults from the extension's **Vaults** field show up there too.

## The first unlock

Ask something like *"What's in my Taxes vault?"*. The vault is locked, so Claude asks to unlock it:

- **On a Mac,** a password box shows, saying which vault and why Claude wants it. Type the vault password and press OK. Claude carries on.
- **On Windows and Linux,** Claude gives you a link. Open it, type the password on that page, choose how long the vault stays open (**15 minutes**, **1 hour**, **Until I lock it** or **Until the AI app closes**), press **Unlock**, and tell Claude it's done. Either way the password stays on your computer: Claude never sees it, and it never goes through the chat. The keys are kept only in memory, and are wiped when the vault locks or Claude Desktop closes.

## What you get

All 23 tools ([tools.md](tools.md)): list, read, find, write, move, copy, trash, undo, versions, and the health check. Every change is logged and keeps what it replaced. Ask *"what did you change today?"* or *"undo that"*. Deleting for good only happens when you empty the trash, and you approve that yourself, outside the chat.

When every vault is **Read only** or **Hidden from AI**, the tools that change files are left out, so Claude shows fewer tools. After changing a mode to or from read only, restart Claude Desktop.

## Fewer permission clicks

Claude asks before it uses each tool. Only you can change that: Encryptor can't allow itself. Click **Always allow** the first time a tool asks, and Claude stops asking for that one. Or set them all at once in Claude's settings, under the extension's tools.

A sensible choice:

- **Always allow** the tools that only read: `vaults`, `list_folder`, `find`, `read_file`, `file_info`, `recent_changes`, `versions`, `trash_list`, `health_check`, `locate`, `decrypt_name`.
- **Always allow** the ones that change files too, if you're comfortable: every change can be undone.
- Deleting for good (`empty_trash`) still asks you in its own box, whatever you choose here.

## Change the settings

**Settings → Extensions → Encryptor MCP → Configure**: change the vaults or the minutes, then restart the extension.

Most things are easier on the control center, and what you save there wins over the extension's fields:

- Once you press **Save** under **Auto-lock** on the control center, the extension's **Lock after minutes without use** no longer applies.
- A vault from the **Vaults** field that you rename, move or remove on the control center keeps your change.

All settings: [settings.md](settings.md).

## Where things are

| What | Where |
|---|---|
| Your vaults | Where they were, encrypted as before. They keep working in Cryptomator |
| Changes, earlier versions and the trash | Inside each vault, in the encrypted hidden folder `.encryptor` |
| The control center's settings, fingerprints and read logs | `~/.config/encryptor-mcp/state` (Windows: `C:\Users\you\.config\encryptor-mcp\state`) |
| Vault passwords and keys | Nowhere on disk. Keys live in memory only |

## Update

Download the newest [`encryptor-mcp.mcpb`](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest/download/encryptor-mcp.mcpb) and open it again. Your vaults, settings and changes stay. See [updates.md](updates.md).

## Remove

**Settings → Extensions**, then remove **Encryptor MCP**. To remove its settings too, delete `~/.config/encryptor-mcp`.

Your vaults are not touched. The `.encryptor` folder stays inside each vault: delete it in Cryptomator if you don't want it.

## If it doesn't work

<details>
<summary><b>The tools don't appear</b></summary>

Check the extension is turned on, then start a new chat. Restart Claude Desktop if needed.

</details>

<details>
<summary><b>No vaults</b></summary>

Open the control center and add one, or fill in **Vaults** under **Configure**.

</details>

<details>
<summary><b>The unlock page doesn't open</b></summary>

Ask Claude to unlock again. On a Mac a password box shows instead.

</details>

<details>
<summary><b>Nothing happens, or an error about uv or Python</b></summary>

Claude Desktop sets these up itself. Make sure it's up to date, and that your computer can reach the internet for the first start.

</details>

More in [troubleshooting.md](troubleshooting.md).

## How it's built

The `.mcpb` file is a zip of this project plus [`extension/manifest.json`](../extension/manifest.json). Claude Desktop runs it with uv, from the exact package versions in `uv.lock`, with the command `encryptor-mcp stdio`. Each release builds it, checks it with Anthropic's own validator, and attaches it to the release ([the workflow](../.github/workflows/extension.yml)). To build it yourself: `python3 scripts/build_mcpb.py` (the file lands in `dist/`).

## What we tested

| Step | Tested |
|---|---|
| The file builds and passes Anthropic's own checker (`mcpb validate`) | Yes |
| Encryptor itself, over stdio, with the official MCP Python client | Yes (macOS, automated tests) |
| Installing it in Claude Desktop, the tools loading, unlocking with the Mac password box, reading, writing, undo, trash, health check, lock | Yes (macOS, 2026-10-17) |
| Windows and Linux | Not yet |
