# If something goes wrong

> [!TIP]
> Start here:
> - Ask your AI: *"Which Encryptor vaults can you see?"* It lists every vault it may use, open or locked. If that works, Encryptor runs and your AI app reaches it.
> - Check which version you have: `encryptor-mcp version` in a terminal (a program where you type commands).
> - On the control center, the **About** page shows the version too, and whether a newer one is out.

Each problem below starts with the exact message you see. Click it for why it happens and what to do.

## Unlocking

<details>
<summary>"The vault 'Taxes' is locked. Call unlock to ask the user to open it."</summary>

That's normal. A vault starts locked, and locks again by itself after some time without use. Ask your AI to unlock it, then type the password on the page or in the box that opens.

</details>

<details>
<summary>The unlock page didn't open</summary>

Some AI apps can't open pages by themselves. Then one of these happens instead:

- **On a Mac**, a password box appears.
- **Otherwise**, the AI shows you a link. Open it in a browser on the same computer (on a server, in any browser).

The link works once, for 5 minutes. To always get one way, set `ENCRYPTOR_UNLOCK` to `page`, `box` or `link` ([settings.md](settings.md)).

</details>

<details>
<summary>"Wrong password."</summary>

The password doesn't open this vault. Check Caps Lock and your keyboard layout, and try the password you use in Cryptomator. When only 1 or 2 tries are left, the message says so. Forgot it? See [faq.md](faq.md#passwords-and-keys).

</details>

<details>
<summary>"Too many wrong passwords. Try again in 12 minutes."</summary>

Five wrong passwords for one vault within 15 minutes pause its unlock page, so nobody can guess fast. Wait the minutes it says. Other vaults aren't affected.

</details>

<details>
<summary>"Too many wrong tries. Wait 15 minutes."</summary>

This is about the passphrase of the server version, not a vault password. Five wrong passphrases from one address within 15 minutes pause sign-in from that address. Fifty from anywhere pause every sign-in. It covers both the control center's sign-in and connecting an AI app. Wait 15 minutes. Restarting the server also clears the count.

</details>

<details>
<summary>"This unlock link has expired or was already used. Ask your AI app to unlock the vault again."</summary>

Unlock links work once, for 5 minutes. Ask your AI to unlock the vault again for a fresh one.

</details>

<details>
<summary>"The user cancelled the password box, or it timed out."</summary>

The Mac password box was closed, or nobody typed in it for 5 minutes. Ask your AI to unlock again.

</details>

<details>
<summary>"This vault's key file is missing. Check the vault's folder."</summary>

The vault folder has no `masterkey.cryptomator`. The folder may be the wrong one, or still syncing. The vault's own folder holds `vault.cryptomator`, `masterkey.cryptomator` and a folder called `d`.

</details>

<details>
<summary>"That folder has no vault.cryptomator: choose the vault's own folder."</summary>

You picked a folder above or inside the vault. Choose the folder that holds `vault.cryptomator`, `masterkey.cryptomator` and `d`.

If the folder has `masterkey.cryptomator` but no `vault.cryptomator`, it's an older vault (format 6 or 7, from before Cryptomator 1.6). Open it once in a current Cryptomator: it offers to upgrade the vault to format 8. Then it works here too.

</details>

<details>
<summary>"This is a Cryptomator Hub vault. Hub vaults aren't supported yet."</summary>

Hub vaults get their key from a Cryptomator Hub server, not from a password. They don't work yet ([roadmap.md](roadmap.md)).

</details>

## Vault folders and sync

<details>
<summary>"No vault called 'Taxes'."</summary>

- The name may be spelled differently: ask *"Which Encryptor vaults can you see?"*
- The vault may be **Hidden from AI**: check its mode on the control center, under the vault's **Settings**.
- On the server version, the vault may not be ticked for this AI app: on the **Vaults** page, under **Connected AI apps**, press **Choose vaults**.

</details>

<details>
<summary>"A folder's encrypted directory is missing (the vault may be incomplete or still syncing)."</summary>

Part of the vault isn't on this disk yet. Wait for your sync app to finish, then try again. If it stays, run the health check: ask *"check the health of my vault"*, or press **Check health** on the vault's page.

</details>

<details>
<summary>Files look missing, or a folder shows as empty</summary>

The vault may still be syncing. Wait for your sync app, then look again. Then run the health check on the vault's page.

</details>

<details>
<summary>Online-only files are slow, or won't open</summary>

iCloud Drive, OneDrive, Dropbox and others can keep files in the cloud only, and fetch them when a program opens them. Encryptor reads the encrypted files like any program, so each read may wait for a download, or fail when you're offline. Set the vault's folder to stay on your device: "Keep Downloaded" (iCloud Drive), "Always keep on this device" (OneDrive), "Make available offline" (Dropbox). See [where-your-vaults-live.md](where-your-vaults-live.md).

</details>

<details>
<summary>"The file's header doesn't check out (changed, or from another vault)."</summary>

The encrypted file is damaged, cut short, or not fully synced. Wait for the sync. If it stays, look for an earlier version: ask *"show earlier versions of this file"*. The health check lists every damaged file.

</details>

<details>
<summary>The health check finds a "conflict" copy</summary>

Your sync app made a copy, like `name (1)`, because two devices changed the same thing before syncing. Its name can't be read here. Open the vault in Cryptomator's desktop app, which sorts these out.

</details>

## Changes and undo

<details>
<summary>"'notes.txt' changed since you read it. Read it again before replacing it."</summary>

Someone else changed the file after the AI read it: you, another app, or a sync. Nothing was overwritten. The AI reads it again and then makes its change.

</details>

<details>
<summary>"'notes.txt' already exists. Read it first and pass its version to replace it, or use append_file."</summary>

The AI tried to make a new file where one already is. That's a guard against overwriting by mistake. The AI reads the file first, then replaces it.

</details>

<details>
<summary>"'notes.txt' changed since then, so undoing would lose newer work."</summary>

The file changed again after that change, so a plain undo would throw away the newer work. Ask for the file's earlier versions instead and pick one: *"show earlier versions of notes.txt"*. Putting one back keeps the current contents too. See [undo-and-backups.md](undo-and-backups.md).

</details>

<details>
<summary>"Another program is changing this vault. Try again in a moment."</summary>

Two changes never run at the same time on one computer. Another AI app, or Finder, was changing the same vault. Try again in a moment.

</details>

<details>
<summary>"More than 60 changes in a minute: slowing down. Try again shortly."</summary>

A brake against runaway changes. Wait a minute. If the AI hit it on its own, check what it was doing: ask *"what changed in my vault?"*, or look at the vault's page.

</details>

<details>
<summary>"Taxes is open read only. If changes are needed, ask the user to lock it and unlock it again without 'read only'."</summary>

You ticked **Read only** when you unlocked it. Lock it (ask your AI, or **Lock now** on the vault's page), then unlock it again without that tick.

</details>

<details>
<summary>"Taxes is set up as read only; nothing in it can be changed here."</summary>

The vault's mode is **Read only**. Change it on the control center, in the vault's **Settings**, under **The AI may**. Then restart your AI app (see "The AI can't change anything after you changed a mode" under [Your AI app](#your-ai-app)).

</details>

<details>
<summary>"Read only for every AI app is on in the control center: nothing can be changed now."</summary>

The switch on **Settings**, under **Safety**, is on. Untick it there. If it says "(set in the setup file)", remove `ENCRYPTOR_READ_ONLY` from your settings file instead ([settings.md](settings.md)).

</details>

<details>
<summary>"This app may only read Taxes. The user can allow changes when connecting it again."</summary>

On the server version, this AI app connected without **It may change files**. On the **Vaults** page, under **Connected AI apps**, press **Choose vaults** next to the app, tick **It may change files**, and press **Save**.

</details>

<details>
<summary>"Deleting for good is switched off for AI apps."</summary>

On **Settings**, under **Safety**, the AI may not ask to delete the trash for good. Empty it yourself on the vault's page, or tick that box again.

</details>

<details>
<summary>"This can't be approved in the chat."</summary>

Deleting for good is never approved with a yes in the chat. Your AI app can't show its own question, and there's no Mac box here. Open the vault's page on the control center, open **Delete the trash for good**, tick the box and press **Delete for good**.

</details>

<details>
<summary>"It's no longer in the trash (the trash was emptied)."</summary>

That item was deleted for good, so the undo can't bring it back. Earlier versions of other files are still there until the trash is emptied.

</details>

## Your AI app

<details>
<summary>The app doesn't show the tools</summary>

- Restart the app after adding Encryptor.
- On a computer, use the full path of the command ([connect-your-ai.md](connect-your-ai.md)).
- Try the command yourself: `encryptor-mcp stdio` should wait silently (Ctrl+C stops it). An error there is the real problem.
- Errors show up in the AI app's own MCP log. Encryptor keeps no log file of its own.

</details>

<details>
<summary>The AI can't change anything after you changed a mode</summary>

When every vault is read only or hidden, Encryptor starts without its write tools (like `write_file` and `move`), so the AI can't even try. Those tools are chosen when your AI app starts Encryptor. After you set a vault to **Read and change**, restart your AI app. On the server version, restart the server.

</details>

<details>
<summary>A vault is open in one AI app but locked in another</summary>

On a computer, each AI app runs its own copy of Encryptor, with its own keys. Unlocking in Claude doesn't unlock it in Cursor. Ask the other app to unlock it too.

</details>

<details>
<summary>"Redirect not allowed" when connecting</summary>

The app's return address isn't on the server's list. Add the app's domain to `ALLOWED_REDIRECT_HOSTS` and restart. That setting replaces the built-in list, so copy the defaults too: `claude.ai,claude.com,chatgpt.com,openai.com,vscode.dev,` then yours ([settings.md](settings.md)).

</details>

<details>
<summary>"This login link expired. Start the connection again in your AI app."</summary>

Login links last 10 minutes. Start connecting again in the AI app. The same goes for "This connection link expired."

</details>

<details>
<summary>"Tick at least one vault."</summary>

When you connect an AI app to the server, tick at least one vault it may ask for. If the list is empty, add a vault on the control center first.

</details>

<details>
<summary>The app was connected, now it isn't</summary>

Its key renews by itself as long as you use the app at least once every 90 days. After 90 days without use, or after **Disconnect** on the control center, connect it again.

</details>

<details>
<summary>The unlock page says "An AI app called You..."</summary>

An app sent a name starting with "You". The page marks it, so no app can pose as you. If you didn't expect it, don't unlock.

</details>

## The control center

<details>
<summary>"Open your control center"</summary>

You aren't signed in. On a computer, press **Unlock** next to a vault and type its password, or ask your AI: *"Open my Encryptor control center."* It opens already signed in.

</details>

<details>
<summary>The control center doesn't load, or an old link stopped working</summary>

On a computer, the control center only runs while an AI app runs Encryptor, and its address changes each time. Bookmarks don't work for long. Ask your AI to open it again.

</details>

<details>
<summary>"No browser could be opened here."</summary>

The AI app runs somewhere without a browser. Unlock a vault from the AI, and open the control center from the vault's page.

</details>

<details>
<summary>"This sign-in link expired or was already used."</summary>

Sign-in links work once, for 5 minutes. Ask your AI to open the control center again, or unlock a vault on the sign-in page.

</details>

<details>
<summary>"This form is out of date. Reload the page and try again."</summary>

The page was open for a long time, or you signed in again elsewhere. Reload it, then do it again. "This form didn't come from this page." means the same: reload.

</details>

<details>
<summary>"Can't show this here"</summary>

Only pictures (PNG, JPEG, GIF, WebP) and text show in the browser. Other files, PDFs too, can only be downloaded. A download is saved decrypted.

</details>

## The server

<details>
<summary>`serve` says "Set a passphrase first"</summary>

The server version needs a passphrase of 8 characters or more. Run `encryptor-mcp set-passphrase`, or set `LOGIN_PASSPHRASE` in your settings file.

</details>

<details>
<summary>"PUBLIC_URL must start with https:// : vault passwords are typed on these pages."</summary>

Plain `http://` is refused on any address other than your own computer, because vault passwords are typed on these pages. Use the Docker Compose setup, where Caddy gets the HTTPS certificate for you ([setup-own-server.md](setup-own-server.md)).

</details>

<details>
<summary>"error while attempting to bind on address ... address already in use" when starting `serve`</summary>

Something else uses port 8767, maybe another copy of Encryptor. Stop it, or set `PORT` to another number.

</details>

<details>
<summary>"Invalid Host header"</summary>

The server got a request for an address it doesn't expect. Set `PUBLIC_URL` to the exact public address, and make sure your proxy passes the original `Host` header through.

</details>

<details>
<summary>Every vault is locked after a restart</summary>

That's on purpose. Keys live only in memory, so a restart locks everything. Unlock again.

</details>

<details>
<summary>Settings or connected apps vanish after a restart</summary>

The data folder isn't kept. With Docker, `/data` must be a volume, as in `docker-compose.yml`.

</details>

## Mac Finder

<details>
<summary>Show in Finder doesn't appear</summary>

It's on the page of an open vault, on a Mac only. It's hidden when `ENCRYPTOR_FINDER=off` is set.

</details>

<details>
<summary>"macOS didn't mount the vault. Try again, or use Browse files."</summary>

macOS refused to show the vault as a drive. Press **Show in Finder** again. If it keeps failing, use **Browse files** on the vault's page instead.

</details>

<details>
<summary>The vault vanished from Finder</summary>

It's removed when the vault locks: after time without use, when you lock it, or when the AI app closes. Unlock it again, then **Show in Finder**.

</details>

<details>
<summary>"Files over 512 MB can't be saved through Finder."</summary>

Files saved from Finder are held in memory, never on disk, so there's a size limit. Save big files into the vault with Cryptomator.

</details>

<details>
<summary>Finder can't save or delete anything</summary>

The vault is open read only. Lock it and unlock it again without **Read only**, or change its mode. Deleting in Finder puts things in the vault's trash, where you can restore them.

</details>

## Still stuck?

Open an issue with the [bug report form](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/issues/new?template=bug_report.yml). Include:

- what you asked the AI, or did on the control center, and what happened
- how you run it (computer, Claude Desktop extension, Docker) and which AI app
- `encryptor-mcp version`, and your system (like macOS 15)
- the exact message

Leave out vault passwords, recovery keys, your passphrase, file names and anything from your files. Issues are public. For a security problem, report it [privately](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/security/advisories/new) instead.
