# Troubleshooting

**"The vault 'X' is locked. Call unlock..."** The AI needs you to unlock it. Ask it to unlock the vault, then type the password on the page that opens.

**The unlock page didn't open.** Your AI app may not open pages by itself. It then shows a link (open it on the same computer), or on a Mac a password box appears.

**"This unlock link has expired or was already used."** Links work once, for 5 minutes. Ask the AI to unlock again.

**"Too many wrong passwords. Try again in N minutes."** Five wrong tries pause that vault for 15 minutes.

**"That folder has no vault.cryptomator."** Choose the vault's own folder (the one with `vault.cryptomator`, `masterkey.cryptomator` and `d` inside).

**"... changed since you read it."** The file changed (another device, a sync). The AI reads it again and retries.

**The control center says "Open your control center".** You're not signed in: unlock a vault there with its password, or ask your AI app to open it.

**Files look missing or a folder shows as empty.** The vault may still be syncing. Then run the health check on the vault's page.

**Show in Finder doesn't appear.** It's Mac only, and only for open vaults. It can be turned off with `ENCRYPTOR_FINDER=off`.

**On a server: "PUBLIC_URL must start with https://".** Vault passwords are typed on these pages, so plain http is refused on the internet. Use the Compose file (Caddy gives you HTTPS).

**Still stuck?** [Open an issue](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/issues/new). Never paste passwords, recovery keys or file contents.
