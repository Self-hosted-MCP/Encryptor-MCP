# Tools the AI can use

Your AI app picks these by itself when you ask in plain words. Tools that change files are left out completely when every vault is set to read only.

Never part of any tool: vault passwords, recovery keys, creating vaults, the read log and the sign-in log. Those are only on your control center.

| Tool | What it does | Description |
|---|---|---|
| `vaults` | reads | The vaults this app may use: open or locked, read only or not, and when an open one locks by itself. |
| `unlock` | changes, can be undone | Ask the user to open a locked vault. The user types the password on their own computer (a local page or a password box), never in this chat, and chooses how long it stays open. purpose: a few words on why, shown to the user. Never ask the user for the password yourself. |
| `lock` | changes, can be undone | Lock a vault now (or every open vault, when vault is left empty). The keys are wiped from memory. |
| `control_center` | reads | Open the Encryptor MCP control center for the user: all their vaults (unlock, lock), what changed (undo), the trash, and settings (which vaults, what the AI may do, auto-lock). On this computer it opens in the user's own browser; the link is never shown here. |
| `list_folder` | reads | List a folder in an open vault: names, kinds and sizes. folder: a path like 'Taxes/2025' ('/' is the top). |
| `read_file` | reads | Read a text file from an open vault. purpose: a few words on why (kept in the log). offset and max_chars read a long file in parts. Pictures and other binary files aren't returned as text. |
| `file_info` | reads | Details of a file or folder in an open vault: kind, size, last change, and where it's stored encrypted. |
| `find` | reads | Find files and folders whose name contains some text (any case), in an open vault. |
| `health_check` | reads | Check that an open vault's structure is whole (folders, long names, files), like Cryptomator's own health check, plus files that were cut or changed. Read only: repairs are made by the user on the control center. |
| `locate` | reads | Where a file or folder of an open vault is stored encrypted on disk (relative to the vault's folder): handy for sync conflicts or backups. |
| `decrypt_name` | reads | The real path of an encrypted path inside an open vault, like d/AB/CDEF.../name.c9r (as shown by a sync app or a file browser). |
| `write_file` | changes, can be undone | Create a text file, or replace one. To replace, pass the version that read_file or file_info gave you; if the file changed since, nothing is written. The old contents are kept and the change can be undone. purpose: a few words on why (kept in the change log). confirm: only when a previous answer asked for it. |
| `append_file` | changes, can be undone | Add text to the end of an existing text file. The previous contents are kept and it can be undone. |
| `make_folder` | changes, can be undone | Create a folder (its parent folder must exist). |
| `move` | changes, can be undone | Move or rename a file or folder, within one vault. Nothing is overwritten: the new place must be free. |
| `copy_file` | changes, can be undone | Copy a file to a new name or folder in the same vault (stays encrypted the whole time). |
| `trash` | changes, can be undone | Put a file or folder in the vault's trash. It stays encrypted in the vault and can be taken back out with undo. Deleting for good is only possible by emptying the trash, which the user approves. |
| `trash_list` | reads | What's in the vault's trash: each item's id, original path and when it was put there. |
| `empty_trash` | deletes for good, you approve | Delete for good: one item from the trash (its id from trash_list), or the whole trash when item is empty. This can't be undone, so the user approves it themselves outside the chat. |
| `recent_changes` | reads | The latest changes in a vault: when, which app, why, and whether they were undone. |
| `undo` | changes, can be undone | Undo one change (its id from recent_changes), or the latest one. Refuses when the file changed since, so newer work is never lost. |
| `versions` | reads | Earlier versions of a file kept by its changes, newest first, for restore_version. |
| `restore_version` | changes, can be undone | Put back an earlier version of a file (its id from versions). The current contents are kept too. |
