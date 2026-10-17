# Where your vaults live

Encryptor MCP opens a vault the way Cryptomator does: straight from its folder. It needs no account at any storage service. The folder has to be reachable as a normal folder, on your computer or on your server.

Works with Cryptomator vaults. Not made by or affiliated with Cryptomator.

## Find the vault folder

A vault folder is the one with a file named `vault.cryptomator` in it. Next to it you'll see `masterkey.cryptomator` and a folder named `d`. That's the folder you add on the control center (**Settings**, **Add a vault**, **Vault folder**), not a folder inside it.

```
Taxes/                    ← add this folder
├── vault.cryptomator
├── masterkey.cryptomator
└── d/
```

To find it, look in Cryptomator: its vault list shows where each vault is kept. Or search your computer for `vault.cryptomator`.

Encryptor opens vaults made with Cryptomator 1.6 or later (vault format 8). No Cryptomator vault yet? Use **Create a new vault** on the control center: Cryptomator can open it too.

## Storage at a glance

As of October 2026. "Computer" means Encryptor on the same computer as your AI app ([setup-computer.md](setup-computer.md)). "Server" means your own server ([setup-own-server.md](setup-own-server.md)).

| Storage | On a computer | On your server | Notes |
|---|---|---|---|
| **Nextcloud** | Yes, in the Nextcloud desktop app's folder | Yes: the Nextcloud command-line client syncing into `./vaults`, or rclone (WebDAV) | With virtual files on, keep the vault folder **always available on this device** |
| **Dropbox** | Yes, in your Dropbox folder | Yes: the Dropbox Linux app, or rclone | Make the vault folder available offline, not online-only |
| **iCloud Drive** | Yes, on a Mac (and in iCloud for Windows) | Not easy: there's no iCloud app for Linux | Turn off **Optimize Mac Storage**, or choose **Keep Downloaded** for the vault folder |
| **Google Drive** | Yes, with Google Drive for desktop | Yes, with rclone | In streaming mode, make the vault folder available offline (or choose mirroring) |
| **OneDrive** | Yes, in your OneDrive folder | Yes, with rclone | With Files On-Demand, choose **Always keep on this device** for the vault folder |
| **Syncthing** | Yes | Yes, syncing into `./vaults` | Real files on both sides, nothing online-only |
| **USB or external disk** | Yes, while it's plugged in | Yes, if it's plugged into the server and mounted into `./vaults` | A vault on a disk that's unplugged can't be opened |
| **NAS or network share (SMB)** | Yes, once the share is connected | Yes: mount the share on the server and point `./vaults` at it | Slower than a local disk. Keep the share connected while a vault is open |
| **WebDAV** | Yes, as a connected network drive, or with rclone | Yes, with rclone | A WebDAV drive can be slow with many files |
| **S3 or other cloud storage** | With `rclone mount` | Yes, with rclone | Any storage rclone supports ([rclone's list](https://rclone.org/overview/)) |

### Three things to watch with synced folders

- **Online-only files.** OneDrive's Files On-Demand, iCloud's **Optimize Mac Storage**, Dropbox's online-only files and Google Drive's streaming can leave placeholders instead of real files. Encryptor needs the real encrypted files: make the vault folder always kept on the device.
- **Sync conflict copies.** When two places change the same file before syncing, sync apps keep both, with a name like `name (1)` or `sync-conflict`. Inside a vault those copies can't be opened by name. The [health check](#after-a-sync-conflict) finds them.
- **Two computers writing at once.** Encryptor never runs two changes at the same time on one computer. But it can't see another computer. If two computers (or Cryptomator and Encryptor on different computers) change the same synced vault at the same moment, you can get conflict copies. Let one side finish and sync first.

Each computer also keeps its own fingerprints and read log. A normal save made on another computer shows in the health check as a harmless note (**Harmless**), never as a problem.

## On your server, with rclone

On your own server, `docker-compose.yml` has an optional `rclone` service. It shows a cloud storage as the `./vaults` folder, so Encryptor reads and writes it like any folder. The files stay encrypted on the way and in rclone's cache: only Encryptor decrypts them, in memory.

1. Set up a remote named `vaults` once, with `rclone config` (Nextcloud is **WebDAV**, plus S3, Google Drive, Dropbox, OneDrive and many more).
2. Save its config as `./rclone/rclone.conf`, next to `docker-compose.yml`.
3. Start with the profile:

   ```bash
   docker compose --profile rclone up -d --build
   ```

rclone mounts the top of the remote (`vaults:`) at `/vaults`. So a vault in the folder `Taxes` at the top of your storage is `/vaults/Taxes` on the control center. If your vaults sit deeper, for example in `Cryptomator/`, change `vaults:` to `vaults:Cryptomator` in the `rclone` service's `command` line.

It runs with `--vfs-cache-mode writes`: rclone keeps files being saved in its cache and uploads them after. Give it a moment before you open the same vault elsewhere. Details: [setup-own-server.md](setup-own-server.md#vaults-in-cloud-storage-rclone).

> [!NOTE]
> We haven't tried the rclone service end to end yet. The setup follows rclone's own docs.

## Not supported

- **Cryptomator Hub vaults,** and vaults whose key file is kept outside the vault folder.
- **Older vaults** (format 6 and 7, from Cryptomator before 1.6). A current Cryptomator can upgrade them.
- **Storage you can only reach in a browser,** with no sync app and no rclone support. Encryptor needs a folder.
- **Vault folders at a hosting company** (Railway, Render and the like). The keys would sit in that company's memory, and your vault folders would have to be on its disk. See [roadmap.md](roadmap.md).

## After a sync conflict

Ask your AI: *"Run a health check on my Taxes vault."* Or press **Check health** on the vault's page in the control center. It looks for:

- **Sync conflict copies,** marked **Worth a look**. Cryptomator's desktop app can sort these out.
- **Damaged files,** for example a file cut short during a sync.
- **Files cut short or swapped** since Encryptor last saw them, from its private fingerprint list.
- **Leftovers** from an interrupted save, and broken folder links.

When some problems can be fixed safely, the vault's page shows a **Repair** button with how many. Nothing is changed until you press it. The health check itself only looks.

Something you changed went wrong? Every change your AI made through Encryptor can be undone: [undo-and-backups.md](undo-and-backups.md).
