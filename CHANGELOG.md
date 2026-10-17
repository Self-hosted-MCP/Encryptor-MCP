# Changelog

## 0.1.0 (2026-10-16)

First version.

- Opens Cryptomator vaults (format 8, both cipher modes) for any MCP app: list, find, read, write, append, folders, move, copy, trash.
- You unlock on a page in your browser (or a Mac password box); the AI never sees the password. Keys only in memory; auto-lock.
- Every change an AI app makes is logged inside the vault, with versions, trash and undo. Deleting for good needs your approval outside the chat. Read only per vault or for every AI app.
- The control center: vaults, browse files, record with undo, trash, health check, read log, settings, activity, about. Sign in with a vault password or from your AI app; on a server with a passphrase.
- Vault tools: create a vault, change its password, recovery key (the same as Cryptomator's), reset with it.
- Health check (like Cryptomator's, plus damaged files and leftovers) with safe repairs; a fingerprint list that catches cut and swapped files; a private, tamper-evident read log.
- Show in Finder (Mac), decrypted only in memory.
- The web version (`encryptor-mcp serve`): OAuth with your passphrase, per-app vault choice, Docker Compose with HTTPS and optional rclone for cloud storage.
- Claude Desktop extension, and a Claude Code plugin.
- Terminal commands: `setup` (add vaults), `check` (settings and vault folders, opens nothing) and `update` (the newest release).
- A ready-made Docker image for each release (amd64 and arm64), one-click Railway and Render setups, an update script for Docker Compose, and an opt-in weekly update for forks.
