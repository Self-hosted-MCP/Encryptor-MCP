# Setup on your own server

Run Encryptor MCP on a VPS or a computer at home, to use your vaults from your phone, claude.ai, ChatGPT and apps anywhere. You get your own address with HTTPS, a passphrase, and the same control center as on a computer. About 15 minutes if you're used to a terminal and a domain.

Works with Cryptomator vaults. Not made by or affiliated with Cryptomator.

> [!WARNING]
> While a vault is open, its keys are in the server's memory. Whoever controls the server could read them. Use a server only you control. See [threat-model.md](threat-model.md).

## What you need

- A server with [Docker](https://docs.docker.com/engine/install/): any VPS, a home server, or a Raspberry Pi 4 or newer. The smallest plan is plenty.
- A domain or subdomain you control, for example `vault.example.com`.
- Your vault folders on that server: synced there by Nextcloud, Syncthing and the like, or reached through rclone ([below](#vaults-in-cloud-storage-rclone)). See [where-your-vaults-live.md](where-your-vaults-live.md).
- A passphrase you make up, 8 characters or more (longer is better). It locks your control center, and you type it once when you connect an AI app. Save it in your password manager.

## With Docker Compose (includes free HTTPS)

[`docker-compose.yml`](../docker-compose.yml) runs two containers: Encryptor MCP, and [Caddy](https://caddyserver.com), which gets and renews the HTTPS certificate by itself.

```
 AI apps, your browser  ──https──►  Caddy (ports 80, 443)  ──►  Encryptor (port 8767, private)  ──►  ./vaults
                                    free certificate,                  │                            (shown as /vaults)
                                    renewed by itself                  ▼
                                                              encryptor-data volume (/data)
                                                     (settings, connected apps, sign-ins, logs)
```

### 1. Point your domain at the server

In your DNS settings, add an `A` record for `vault.example.com` with your server's IP address. Ports 80 and 443 must be open.

### 2. Get the code and settings

```bash
git clone https://github.com/Self-hosted-MCP/Encryptor-MCP.git
```

```bash
cd Encryptor-MCP
```

```bash
cp .env.example .env
```

### 3. Fill in `.env`

Open `.env` and set two lines:

```
ENCRYPTOR_DOMAIN=vault.example.com
LOGIN_PASSPHRASE=a long passphrase only you know
```

`ENCRYPTOR_DOMAIN` is the name only, without `https://`. Then make the file private:

```bash
chmod 600 .env
```

<details>
<summary><b>Keep only a hash of the passphrase instead</b></summary>

`encryptor-mcp set-passphrase` stores a scrambled version (hash) of your passphrase, so the plain one is in no file. In Docker it writes `LOGIN_HASH` into `/data/.env`, inside the `encryptor-data` volume (not the `.env` next to `docker-compose.yml`).

1. Build the image:

   ```bash
   docker compose build
   ```

2. Choose the passphrase. It asks twice:

   ```bash
   docker compose run --rm encryptor encryptor-mcp set-passphrase
   ```

   You should see `Saved (only its hash) in /data/.env.`

3. Remove the `LOGIN_PASSPHRASE=` line from your `.env` (the hash wins anyway, but then no plain copy is left).

To change it later, run step 2 again and then `docker compose restart encryptor`.

</details>

### 4. Put your vault folders in place

Put your vault folders in `./vaults`, next to `docker-compose.yml`. Inside the container they show up as `/vaults/<folder name>`, for example `/vaults/Taxes`. To use another folder, change `./vaults` under `volumes` in `docker-compose.yml`.

Encryptor runs as user number `10001` inside the container. That user must be able to read and write the vault folders, for example:

```bash
sudo chown -R 10001 vaults
```

If a sync app on the server owns those files, give user `10001` write access in a way that keeps your sync app working (a shared group, for example).

### 5. Start it

```bash
docker compose up -d --build
```

The first start builds the image and gets the certificate. It takes a few minutes.

### 6. Check it

Open `https://vault.example.com/health` in a browser. It shows `ok`. To see what it's doing:

```bash
docker compose logs -f encryptor
```

You should see a line like `Control center: https://vault.example.com/  ·  AI apps connect to: https://vault.example.com/mcp`.

To check your settings and vault folders without opening any vault:

```bash
docker compose run --rm encryptor encryptor-mcp check
```

Run Encryptor's commands with `docker compose run --rm encryptor ...` as above. `docker compose exec` runs them as the system's admin user (root), which can leave files the server can't read; if you use `exec`, add `-u encryptor`.

### 7. Add your vaults

Open `https://vault.example.com`, type your passphrase and press **Sign in**. Go to **Settings**. Under **Add a vault**, type a **Name** and the **Vault folder** as the container sees it (`/vaults/Taxes`), choose what **The AI may** do, and press **Add vault**. No vault yet? Use **Create a new vault**.

### 8. Connect your AI apps

Your AI app's server address is `https://vault.example.com/mcp`. The first time, a login page opens: tick which vaults the app may ask for, choose whether it may change files, and type your passphrase. Every app, step by step: [connect-your-ai.md](connect-your-ai.md).

When the AI needs a vault, you unlock it on the server's page, in your browser, over HTTPS. The keep choices are **15 minutes**, **1 hour** and **Until I lock it** (never more than 12 hours, or what you set in `ENCRYPTOR_MAX_HOURS`). **Until the AI app closes** isn't offered on a server.

## Vaults in cloud storage (rclone)

Your vaults can stay in cloud storage (Nextcloud or any WebDAV, S3, Google Drive, Dropbox and more): the optional `rclone` service in `docker-compose.yml` shows that storage as the `./vaults` folder. The files stay encrypted on the way. Decrypting happens only in Encryptor's memory.

1. Install [rclone](https://rclone.org/install/) and set up a remote called `vaults`:

   ```bash
   rclone config
   ```

2. Save its config file as `./rclone/rclone.conf`, next to `docker-compose.yml`. `rclone config file` shows where rclone saved it.
3. Start everything with the `rclone` profile:

   ```bash
   docker compose --profile rclone up -d --build
   ```

Then add the vaults as in step 7: a vault at `vaults:Taxes` in rclone is `/vaults/Taxes` in Encryptor. More, and the limits: [where-your-vaults-live.md](where-your-vaults-live.md#on-your-server-with-rclone).

## Behind your own reverse proxy

Already run nginx, Traefik, Coolify or similar? Skip Caddy and run only Encryptor:

- **Build:** the [`Dockerfile`](../Dockerfile) in the repository root (amd64 and arm64). There's no ready-made image yet.
- **Port:** `8767` (or set `PORT`).
- **Storage:** a volume at `/data`, and your vault folders at `/vaults`.
- **Environment:** `PUBLIC_URL=https://your-domain` and `LOGIN_PASSPHRASE` (or a hash, as above).
- **Health check:** `GET /health` answers `ok`.

<details>
<summary><b>nginx instead of Caddy</b></summary>

Add a port to the `encryptor` service in `docker-compose.yml`, so only this server can reach it:

```yaml
    ports:
      - "127.0.0.1:8767:8767"
```

Start only that service with `docker compose up -d --build encryptor`. Then point a site at it:

```nginx
server {
    listen 443 ssl;
    server_name vault.example.com;
    # ssl_certificate and ssl_certificate_key as for your other sites

    location / {
        proxy_pass http://127.0.0.1:8767;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_http_version 1.1;
        proxy_buffering off;          # the MCP connection streams its answers
        proxy_read_timeout 3600s;
    }
}
```

</details>

## Without Docker

Install it as on a computer ([setup-computer.md](setup-computer.md), steps 1 and 2). Then:

1. Choose the passphrase. Only its hash is saved, in `~/.config/encryptor-mcp/.env`:

   ```bash
   encryptor-mcp set-passphrase
   ```

2. Add your address to that file:

   ```
   PUBLIC_URL=https://vault.example.com
   ```

3. Start it:

   ```bash
   encryptor-mcp serve
   ```

It listens on `127.0.0.1:8767`. Put any HTTPS reverse proxy (Caddy, nginx, Traefik) in front of it. It refuses to start with a public address that isn't `https://`, because vault passwords are typed on its pages.

<details>
<summary><b>Run it as a systemd service</b></summary>

Save as `/etc/systemd/system/encryptor-mcp.service` (replace `you` with the user that installed it):

```ini
[Unit]
Description=Encryptor MCP
After=network-online.target

[Service]
User=you
ExecStart=/home/you/.local/bin/encryptor-mcp serve
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then turn it on:

```bash
sudo systemctl enable --now encryptor-mcp
```

Its messages: `journalctl -u encryptor-mcp`.

</details>

## Backups

Your vaults are normal folders: back them up as you do now. They stay encrypted, and the `.encryptor` folder inside each one holds the changes, earlier versions and trash.

The `/data` volume (`encryptor-data`) keeps everything else that must survive a restart: the control center's settings, connected AI apps, remembered sign-ins, fingerprints and read logs, and `/data/.env` if you used `set-passphrase`. Keys and vault passwords are never in it. To copy it out:

```bash
docker compose cp encryptor:/data ./data-backup
```

Keep that copy private.

## Update

```bash
git pull
```

```bash
docker compose up -d --build
```

A restart locks every open vault. More in [updates.md](updates.md).

## Stop or remove it

- **Stop:** `docker compose down`. Your settings and connected apps are kept in the volume.
- **Remove everything:** `docker compose down -v` also deletes the `/data` volume and Caddy's certificates. Then remove the connector from your AI apps.

Your vaults are not touched. The `.encryptor` folder stays inside each vault: delete it in Cryptomator if you don't want it.

## What we tested

| Step | Tested |
|---|---|
| Docker Compose end to end on a Mac (Colima): build, Caddy with HTTPS, `/health`, sign in, add a vault from `./vaults`, an AI app connecting over OAuth, unlock, read, write, undo, lock, then a clean health check of the vault | Yes (2026-10-17) |
| `encryptor-mcp check` inside the container | Yes |
| The control center in a browser, desktop and phone width, light and dark | Yes (macOS) |
| A real domain with a public certificate (the test used `localhost`, where Caddy makes its own) | Not yet |
| `set-passphrase` inside the container (it asks for the passphrase on screen) | Not yet |
| The rclone service, the folder owner steps, nginx, systemd | Not yet: steps follow the official docs of each |
| Each AI app over the internet | Not yet |
