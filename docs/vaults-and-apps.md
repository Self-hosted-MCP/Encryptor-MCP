# Vaults and apps

You decide what the AI may see and change, in two layers: a mode for each vault, and, on a server, a choice for each AI app. On top of that, a vault is only usable while you've unlocked it with its password.

Works with Cryptomator vaults. Not made by or affiliated with Cryptomator.

## What the AI may do with each vault

| Mode | On the control center | The AI may |
|---|---|---|
| `full` (the default) | **Read and change** | Read, add, change, move and trash files. Every change the AI makes can be undone |
| `read` | **Read only** | Read and search, but change nothing |
| `hidden` | **Hidden from AI** | Nothing: the vault never shows up, not even its name. You can still open it on the control center |

Set the mode in one of these places:

- **The control center:** **Settings**, then **Settings** next to the vault, then **The AI may**. Press **Save**.
- **The settings file** (`~/.config/encryptor-mcp/.env`) or an environment variable:

  ```
  ENCRYPTOR_MODES=Notes=read,Health=hidden
  ```

  Vault names work in any capitals. A mode the program doesn't know becomes `read`, the safe one. Once you change a mode on the control center, the page's choice wins.

When you change a mode while a vault is open: a vault now **Read only** stays open, read only. A vault now **Hidden from AI** stays open for you on the control center, but the AI can't see it.

> [!NOTE]
> When every vault is **Read only** or **Hidden from AI**, the AI app doesn't even get the tools that change files. After setting one to **Read and change**, restart the AI app. See [tools.md](tools.md#limits).

## When you unlock

The unlock page has its own **Read only: the AI can look, not change** box. Tick it, and the vault stays read only until it locks, whatever its mode. Handy for a quick look at a vault you normally let the AI change.

## The default vault

With more than one vault, the AI names the one it means. To let it leave that out, pick a default: in the vault's settings, tick **Default vault: the AI uses it when you don't name one** and press **Save**. The `vaults` tool then marks it as the default.

Without a default, the AI asks you which vault when it isn't clear.

## Several vaults

Add as many vaults as you like. Each has its own name, folder, mode, password and auto-lock time.

**How the AI tells them apart:** by name. The `vaults` tool lists every vault the app may use, with whether it's open, read only, and the default. Names work in any capitals. A hidden vault and a vault this app wasn't given look exactly the same to the AI: "No vault called ...". So the AI can't even find out that it exists.

Names are up to 60 characters, without `;`, `=`, `,` or slashes.

**Several AI apps on one computer** each run their own copy of Encryptor. A vault you unlock in Claude Desktop is still locked in Cursor, and the other way round.

## Auto-lock for each vault

Every vault locks by itself after some time without use. Set the time for all vaults on the control center (**Settings**, **Auto-lock**): 5, 10, 15, 30 or 60 minutes. The default is 10.

A vault can have its own time too: in its settings, **Auto-lock**, choose a time or **Same as all vaults**. Use a short one for your most private vault.

Whatever you choose, no vault stays open longer than 12 hours (`ENCRYPTOR_MAX_HOURS`). More: [settings.md](settings.md#unlocking-and-auto-lock).

## Adding a vault, or creating one

| | Add a vault | Create a new vault |
|---|---|---|
| **For** | A Cryptomator vault you already have | A brand new, empty vault |
| **On the control center** | **Settings**, **Add a vault** | **Settings**, **Create a new vault** |
| **You give** | A **Name**, the **Vault folder** and what **The AI may** do | A **Name**, **Where** to make it, a **New password** twice and what **The AI may** do |
| **What happens** | Nothing is copied or moved: Encryptor points at the folder | A folder named after the vault is made there, and you see its **recovery key** once |

**The vault folder** is the one that holds `vault.cryptomator` (and `masterkey.cryptomator`). If you choose a folder above or below it, you'll see "That folder has no vault.cryptomator: choose the vault's own folder."

Vaults made by Cryptomator 1.6 and later work (vault format 8, both cipher modes). Not supported: older vaults (format 6 or 7), Cryptomator Hub vaults, and vaults whose key file is kept somewhere else.

A new vault is a normal Cryptomator vault: open it in Cryptomator on your other devices with the same password. To have it there, create it inside a synced folder (Nextcloud, Dropbox, iCloud Drive and the like). More: [where-your-vaults-live.md](where-your-vaults-live.md).

You can also list vaults in the settings file, with `ENCRYPTOR_VAULTS` ([settings.md](settings.md#vaults)). They show on the control center like the others, and you can rename, move or remove them there. The file itself isn't changed.

**Remove from the list** (in the vault's settings) only takes the vault off Encryptor's list. The vault and its files stay where they are. Add it again anytime.

## Read only for everything

One switch stops every change, by every AI app, in every vault: **Settings**, **Safety**, **Read only for every AI app**. The home page then says so at the top.

To fix it so the page can't turn it off, set `ENCRYPTOR_READ_ONLY=yes` in the settings file or an environment variable.

## Each AI app, on a server

On a computer, AI apps don't sign in: the app that started Encryptor may use it, and only the vault modes apply.

On a server, each AI app connects with your passphrase. The connect page asks:

1. **Vaults it may ask for:** tick the vaults this app may use. Nothing is ticked at first. Hidden vaults aren't listed.
2. **It may change files (every change it makes can be undone):** unticked at first. Unticked, the app can only read, even in vaults set to **Read and change**.

Each vault still needs its password every time it opens. Connecting only lets the app ask.

Change your mind later on the control center's home page, under **Connected AI apps**: **Choose vaults** to tick other vaults or allow changes, or **Disconnect** to sign the app out. A change counts from the app's next request.

A change only happens when everything allows it: the vault's mode, the app's choice, **Read only for every AI app** being off, and the vault not unlocked as read only.

## The password and the recovery key

The AI never gets either one. No tool takes a password, and none can show a recovery key.

- **You type the password** only on the unlock page, or in the Mac password box. Never in the chat.
- **Change the password** in the vault's settings (**Password**). Cryptomator and your other devices use the new one right away.
- **The recovery key** is 44 words that open the vault if you forget the password. They work in Cryptomator too. You see them once when you create a vault, and again in the vault's settings (**Recovery key**, with the password).
- **Forgot the password?** In the vault's settings, type the recovery key and choose a new password.

Encryptor doesn't store the recovery key anywhere. Keep it in a password manager or on paper. Without the password and the recovery key, nobody can open the vault, not even you.
