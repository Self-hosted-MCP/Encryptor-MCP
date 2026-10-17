# Setup on a hosting company

Always on, so your phone and the Claude or ChatGPT website can reach your vaults any time. No terminal needed. About 10 minutes, a few dollars a month.

> [!CAUTION]
> While a vault is open, its keys live in the memory of a computer the hosting company runs. Anyone who controls that computer could read them, and with them your files. The vault password still never goes through the chat, and the keys are wiped when the vault locks. But if you can, run it on [your own computer](setup-computer.md) or on a [server you control](setup-own-server.md) instead. More in [threat-model.md](threat-model.md).

> [!IMPORTANT]
> On a hosting company, your vaults live on the hosting company's disk, at `/data/vaults`. They don't sync with your other devices by themselves, the way a Nextcloud or Dropbox folder does. To use the vaults you already have in a cloud, use [your own server with rclone](setup-own-server.md) instead.

Every option runs the ready-made image `ghcr.io/s17sh70x2jfl031ag/encryptor-mcp` (or builds this repository's `Dockerfile`) and needs two things:

1. **A passphrase**, `LOGIN_PASSPHRASE`, 8 characters or more. It locks the control center, and AI apps ask for it once when they connect.
2. **A disk at `/data`** that survives restarts. It keeps your vaults, the control center's settings and connected AI apps. Without one, everything is lost at each restart.

The server finds its public address by itself on Railway and Render. Elsewhere, set `PUBLIC_URL` to it.

## One click: Railway

<a href="https://railway.com/deploy/encryptor-mcp"><img src="https://railway.com/button.svg" alt="Deploy on Railway"></a>

1. Press the button. Railway shows the template: this repository, a disk at `/data`, and a public address.
2. Fill in `LOGIN_PASSPHRASE` (8+ characters).
3. Press **Deploy**. When it turns green, open the address it shows and sign in with your passphrase.

## One click: Render

<a href="https://render.com/deploy?repo=https://github.com/s17sh70x2jfl031ag/Encryptor-MCP"><img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render"></a>

1. Press the button (or in Render: **New → Blueprint**, and pick this repository). It reads [`render.yaml`](../render.yaml).
2. Fill in `LOGIN_PASSPHRASE`. Render adds a 1 GB disk at `/data`.
3. Render uses its smallest paid instance, because the free one can't keep a disk and falls asleep.
4. When it's live, open `https://<your-app>.onrender.com` and sign in with your passphrase.

## Railway, by hand

1. In Railway: **New project → Deploy from GitHub repo**, and pick this repository. It builds the `Dockerfile` (see [`railway.json`](../railway.json)). Or **Docker image**: `ghcr.io/s17sh70x2jfl031ag/encryptor-mcp:latest`.
2. **Variables:** `LOGIN_PASSPHRASE` and `PORT=8767`.
3. **Volume:** add one, mounted at `/data`.
4. **Settings → Networking:** generate a public domain on port 8767. **Healthcheck path:** `/health`.
5. Open `https://<your-app>.up.railway.app` and sign in with your passphrase.

## Any other hosting company

Anything that runs a Docker image works (Fly.io, Koyeb, Northflank, Coolify, a NAS, ...):

| What | Value |
|---|---|
| Image | `ghcr.io/s17sh70x2jfl031ag/encryptor-mcp:latest` (or a version, like `:0.1`) |
| Port | 8767 (HTTP; the hosting company adds HTTPS) |
| Health check | `/health` |
| Disk | at `/data` |
| Variables | `LOGIN_PASSPHRASE`, and `PUBLIC_URL=https://your-address` |
| Copies | One. Two copies would each keep their own keys and settings |

The image works on amd64 and arm64. It starts as the user `encryptor` (uid 10001), and gives `/data` to that user first if the disk was mounted as root.

## Then

1. Open `https://your-address` and sign in with your passphrase.
2. **Settings → Create a new vault:** give it a name and the folder `/data/vaults/<name>`, choose a password, and keep the recovery key it shows you somewhere safe.
3. Choose what the AI may do with each vault ([vaults-and-apps.md](vaults-and-apps.md)).
4. Connect your AI apps to `https://your-address/mcp`: [connect-your-ai.md](connect-your-ai.md).

Check it works: `https://your-address/health` says `ok`.

## Stop or remove

- **Pause:** stop the service in the hosting company's dashboard. Open vaults lock.
- **Remove:** delete the service and its disk. This deletes the vaults on that disk too, so copy anything you need first: open each vault and ask your AI to read out what you want to keep, or download files from the vault's page on the control center.

## Updates

`latest` follows the newest release. Redeploy to get it. To stay on one version, use a version tag like `:0.1.0`. See [updates.md](updates.md).

## What we tested

| Step | Tested |
|---|---|
| The image's settings (`serve` on port 8767, `/health`, `/data`), run directly | Yes (macOS) |
| Railway and Render, end to end | Not yet |
| The start script giving a root-owned `/data` to the `encryptor` user | Not yet inside a real hosting company |
