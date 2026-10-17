# Questions people ask

## The basics

<details>
<summary><b>Is it free?</b></summary>

Yes. The software is free and open source (AGPL-3.0 license). Running it on your own computer costs nothing. If you run it on your own server, you pay for that server, as you would anyway. The AI app you use may need its own plan.

</details>

<details>
<summary><b>Can I fork it or use it in my own product?</b></summary>

Yes. It's open source under the [AGPL-3.0](../LICENSE). In plain words:

- You may use it, change it and share it, also for money.
- If you share a changed version, or run a changed version for other people over the internet, you must offer them its source code, under the same license.
- Keep [LICENSE](../LICENSE), [NOTICE](../NOTICE) and the copyright lines, and mark the files you changed.

To update your copy, see [updates.md](updates.md).

</details>

<details>
<summary><b>Is this made by Cryptomator?</b></summary>

No. Works with Cryptomator vaults. Not made by or affiliated with Cryptomator. It reads and writes vaults in the same format as Cryptomator.

</details>

<details>
<summary><b>Do I need Cryptomator installed?</b></summary>

No. Encryptor MCP opens vaults by itself, and it can create new ones on the control center. Keep Cryptomator if you like it: both open the same vaults.

</details>

<details>
<summary><b>Which AI apps work with it?</b></summary>

Any app that speaks MCP (the standard way AI apps use tools): Claude (desktop, website, phone, Claude Code), ChatGPT, Codex, Cursor, VS Code, Gemini CLI and many more. See [connect-your-ai.md](connect-your-ai.md) for each one.

</details>

<details>
<summary><b>Which vaults can it open?</b></summary>

Vaults in format 8, made by Cryptomator 1.6 or later, in both of Cryptomator's encryption modes. Older vaults (format 6 and 7), Cryptomator Hub vaults and vaults whose key file is kept somewhere else don't work yet. Cryptomator itself can upgrade an old vault to format 8. See [where-your-vaults-live.md](where-your-vaults-live.md).

</details>

## Your password and your files

<details>
<summary><b>Does the AI see my vault password?</b></summary>

No. You type it on a page in your own browser, or in a Mac password box. No tool takes a password, so the AI couldn't pass one even if it tried. The same goes for recovery keys and your passphrase. See [safety.md](safety.md).

</details>

<details>
<summary><b>Does my AI's provider see my files?</b></summary>

Only what the AI reads. When it reads a file or lists a folder, that text goes to your AI app, and from there to the company that runs its AI model, like a file you'd paste into the chat. Files it never opens stay encrypted on your disk. Hide a vault, or make it read only, to keep the AI away from it. Details in [privacy.md](privacy.md).

</details>

<details>
<summary><b>Is anything written to disk decrypted?</b></summary>

Encryptor itself never writes your files to disk decrypted: they're decrypted in memory only. The keys stay in memory too. Two things can still leave a readable copy:

- **Files you download** from the control center (the **Download** button) are saved decrypted where your browser saves downloads.
- **Show in Finder** (Mac): Finder reads from memory, but macOS and the apps you open files with may keep their own caches or copies, like previews or autosaves.

Encryptor's own records (changes, earlier versions, trash) are kept encrypted inside the vault.

</details>

<details>
<summary><b>What if the AI changes the wrong thing?</b></summary>

Ask *"undo that"*, or press **Undo** on the vault's page in the control center. Every change your AI makes is logged and keeps what it replaced. Earlier versions of a file can be put back too. See [undo-and-backups.md](undo-and-backups.md).

</details>

<details>
<summary><b>Can every change be undone?</b></summary>

Every change your AI makes can be undone, and so can changes made in Finder. A few things can't:

- **Emptying the trash.** Deleted for good means gone, so Encryptor always asks you first, outside the chat.
- **An undo.** Make the change again instead.
- **An undo that would lose newer work.** If the file changed since, undo refuses. Put back an earlier version instead.
- **Health check repairs,** password and recovery key changes, and creating or removing vaults.
- **Changes made outside Encryptor:** in Cryptomator itself, on another device, or by a sync app.

Keep a backup of your vaults anyway. See [What can't be undone](undo-and-backups.md#what-cant-be-undone).

</details>

<details>
<summary><b>Can it delete my files for good?</b></summary>

Not on its own. The AI can only put things in the vault's trash, and you can take them back out. Deleting for good means emptying the trash, and you approve that yourself outside the chat: in a Mac box, in your AI app's own question, or with the **Delete for good** button on the vault's page. It never works with a yes typed in the chat. You can switch it off completely on **Settings**, under **Safety**.

</details>

<details>
<summary><b>Does Cryptomator still open my vault?</b></summary>

Yes. Encryptor writes files in Cryptomator's own format, so Cryptomator opens them as before. In Cryptomator you'll see one new folder, `.encryptor`: it holds the change log, earlier versions and the trash, encrypted. Leave it there if you want undo to keep working.

</details>

<details>
<summary><b>Why does my vault grow?</b></summary>

Every change keeps the version it replaced, and trashed files stay in the trash. They're kept until you empty the trash. Empty it on the vault's page in the control center when you no longer need them.

</details>

## Vaults, computers and apps

<details>
<summary><b>What about sync conflicts?</b></summary>

If two devices change the same file before syncing, your sync app may make a conflict copy, like `name (1)`. Run the health check (ask *"check the health of my vault"*, or **Check health** on the vault's page): it finds those copies. Cryptomator's desktop app can sort them out. To avoid them, let a sync finish before changing the same files somewhere else.

</details>

<details>
<summary><b>Can I use several vaults?</b></summary>

Yes, as many as you like. Each one gets a mode: **Read and change**, **Read only** or **Hidden from AI**. You can pick a default vault, for when you don't name one. See [vaults-and-apps.md](vaults-and-apps.md).

</details>

<details>
<summary><b>Can I use it on several computers?</b></summary>

Yes. Install it on each one and point it at the same synced vault folder. The change log, versions and trash live inside the vault, so they sync too. Each computer keeps its own read log and its own list of file fingerprints. Two computers changing the same vault at the very same moment aren't protected from each other, so give the sync a moment between them.

</details>

<details>
<summary><b>Can I use several AI apps at once?</b></summary>

Yes. On a computer, each AI app starts its own copy of Encryptor. So a vault you unlocked in one app is still locked in the others: unlock it there too. Changes from both land in the same change log, and two changes never run at the same time on one computer. On a server, each app connects separately, with its own choice of vaults.

</details>

<details>
<summary><b>Does it work offline?</b></summary>

Encryptor itself needs no internet: it works on the vault folders on your disk. Your AI app usually does need the internet, unless it runs a model on your computer. Vaults in a sync folder sync again when you're back online.

</details>

<details>
<summary><b>Can I use it on my phone?</b></summary>

Yes, with the server version: run it on your own server, then connect the Claude or ChatGPT phone app to it. See [setup-own-server.md](setup-own-server.md).

</details>

<details>
<summary><b>What languages does it speak?</b></summary>

The pages and the docs are in English. Your AI answers you in your own language, so you can ask in any language it knows.

</details>

## Passwords and keys

<details>
<summary><b>I forgot a vault's password.</b></summary>

Use the vault's recovery key (44 words). On the control center, open the vault's **Settings**, then **Forgot the password?**. Type the 44 words and a new password. It's the same recovery key as Cryptomator's, so one made in Cryptomator works here too.

</details>

<details>
<summary><b>I lost the recovery key.</b></summary>

If you still know the password, make a new note of the key: on the vault's **Settings**, type the password under **Recovery key** and press **Show**. If you've lost both the password and the recovery key, nobody can open the vault. That's what the encryption is for.

</details>

<details>
<summary><b>I forgot the passphrase (server version).</b></summary>

Set a new one with `encryptor-mcp set-passphrase`. It works at once, no restart needed. With Docker, run it inside the container:

```bash
docker compose run --rm encryptor encryptor-mcp set-passphrase
```

Browsers are signed out. AI apps you already connected stay connected: on the control center's **Vaults** page, under **Connected AI apps**, press **Disconnect** next to any you don't trust.

</details>

## Running it

<details>
<summary><b>Where are my settings?</b></summary>

On a computer, in `~/.config/encryptor-mcp` (on Windows `%USERPROFILE%\.config\encryptor-mcp`): the settings file `.env`, and a `state` folder with what you chose on the control center. With Docker, in `/data`. Most settings are easier to change on the control center. See [settings.md](settings.md).

</details>

<details>
<summary><b>How do I update?</b></summary>

See [updates.md](updates.md). Updates never touch your vaults, settings or change log.

</details>

<details>
<summary><b>How do I remove it?</b></summary>

Remove it from your AI app, then run:

```bash
uv tool uninstall encryptor-mcp
```

Then delete the folder `~/.config/encryptor-mcp`. Your vaults stay where they are and keep working in Cryptomator. The `.encryptor` folder stays inside each vault: delete it in Cryptomator if you want it gone (that also deletes the change log, versions and trash).

</details>

<details>
<summary><b>Can I put it on the internet safely?</b></summary>

The server version is built for that. It refuses to run on a public address without HTTPS. It asks for your passphrase, pauses sign-in after wrong tries, and gives each AI app only the vaults you tick. Each vault still needs its own password whenever it opens. Read [safety.md](safety.md) and [threat-model.md](threat-model.md) first, and keep it updated.

</details>

<details>
<summary><b>Why does the control center use a random address on my computer?</b></summary>

On a computer, the control center runs at `127.0.0.1` (your own computer only) on a free port picked each time. A fixed port could clash with another program, and nothing outside your computer can reach it. It only runs while an AI app runs Encryptor. To open it, ask your AI: *"Open my Encryptor control center."*

</details>

<details>
<summary><b>Why isn't there a guide for hosting companies?</b></summary>

On a hosting company, your vault keys would sit in that company's memory while a vault is open, and your vault folders would have to be on its disks. That defeats the point of an encrypted vault. Run it on your computer, or on a server you control. See [roadmap.md](roadmap.md).

</details>
