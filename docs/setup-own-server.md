# Setup on your own server

Run Encryptor MCP on a VPS or a computer at home, to use your vaults from your phone, claude.ai, ChatGPT and apps anywhere. You get your own address with HTTPS, a passphrase, and the same control center.

You need: a server with Docker, a domain name pointing at it, and your vault folders on that server (synced by Nextcloud, Syncthing and the like, or reached through rclone, see below).

## 1. Get the files

```bash
git clone https://github.com/s17sh70x2jfl031ag/Encryptor-MCP
cd Encryptor-MCP
cp .env.example .env
```

## 2. Settings

Edit `.env`:

```
ENCRYPTOR_DOMAIN=vault.example.com
LOGIN_PASSPHRASE=a long passphrase only you know
```

Use 8 or more characters. To keep only a hash of it instead, run `encryptor-mcp set-passphrase` and use the `LOGIN_HASH=` line it writes.

## 3. Vault folders

Put your vault folders in `./vaults` (they show up inside as `/vaults/<name>`), or change the path in `docker-compose.yml`.

**Vaults in the cloud** (Nextcloud or any WebDAV, S3, Google Drive, Dropbox and more): the optional rclone service shows that storage as the `./vaults` folder. Set up a remote called `vaults` once with `rclone config`, save its `rclone.conf` in `./rclone/`, and start with the `rclone` profile (step 4). The files stay encrypted on the way: decrypting happens only in Encryptor MCP's memory.

## 4. Start

```bash
docker compose up -d
```

With rclone: `docker compose --profile rclone up -d`. Caddy gets the HTTPS certificate by itself.

## 5. Use it

- Open `https://vault.example.com`, sign in with the passphrase, and add your vaults on **Settings** (folder `/vaults/Taxes` and so on), or create new ones.
- In your AI app, add the connector `https://vault.example.com/mcp`. The first time, you type the passphrase and tick which vaults it may ask for, and whether it may change files.
- When the AI needs a vault, you unlock it on the server's page, in your browser, over HTTPS.

## What a server can and can't protect

While a vault is open, its keys are in the server's memory. Whoever controls the server could read them, so use a server only you control. Vaults lock by themselves; a restart locks everything. See [threat-model.md](threat-model.md).

The server refuses to run on a public address without HTTPS. Everything that must survive a restart (settings, connected apps, remembered sign-ins, logs, fingerprints) is in the `/data` volume; keys never are.
