# Tools the AI can use

Your AI app picks these by itself when you ask in plain words ([ideas](examples.md)). You don't need to know their names. This page is for when you want to know exactly what the AI can and can't do.

Never part of any tool: vault passwords, recovery keys, creating a vault, changing a password, the read log and the sign-in log. Those are only on your [control center](control-center.md).

## The 23 tools

Every tool that works on files needs the vault to be open. Paths look like `Taxes/2025/receipt.txt`; `/` is the top of the vault.

| Tool | What it does for you | Parameters | Kind |
|---|---|---|---|
| `vaults` | Lists the vaults this app may use: open or locked, read only or not, how long until an open one locks, and which is the default | none | reads |
| `unlock` | Asks you to open a locked vault. You type the password yourself, never in the chat ([how](#how-unlocking-reaches-you)) | `vault`, `purpose` (why, shown to you) | opens a vault |
| `lock` | Locks a vault now, or every open vault. The keys are wiped from memory | `vault` (empty: all) | locks |
| `control_center` | Opens your control center. On a computer it opens in your browser and the AI never sees the link. On a server it tells the AI your server's address, where you sign in with your passphrase | none | reads |
| `list_folder` | Shows what's in a folder: names, kinds and sizes | `vault`, `folder` (default `/`) | reads |
| `read_file` | Reads a text file. Long files come in parts | `vault`, `path`, `purpose` (kept in the read log), `offset`, `max_chars` | reads |
| `file_info` | Shows a file's or folder's kind, size, last change and where it's stored encrypted | `vault`, `path` | reads |
| `find` | Finds files and folders whose name contains some text, in any capitals | `vault`, `name_contains`, `folder` (default `/`), `limit` | reads |
| `health_check` | Checks the vault is whole, like Cryptomator's own health check, and spots files cut short or swapped. Only looks: you repair on the control center | `vault` | reads |
| `locate` | Tells where a file or folder is stored encrypted, inside the vault folder. Handy for sync conflicts and backups | `vault`, `path` | reads |
| `decrypt_name` | Tells which real file an encrypted name is, like `d/AB/CDEF.../name.c9r` from a sync app | `vault`, `encrypted_path` | reads |
| `write_file` | Makes a new text file, or replaces one. To replace, it needs the version it got when reading, so it never writes over newer work | `vault`, `path`, `content`, `purpose`, `version`, `confirm` | changes, can be undone |
| `append_file` | Adds text to the end of a text file, exactly as given (start it with a line break for a new line) | `vault`, `path`, `content`, `purpose` | changes, can be undone |
| `make_folder` | Makes a folder (the folder it goes in must exist) | `vault`, `path`, `purpose` | changes, can be undone |
| `move` | Moves or renames a file or folder, inside one vault. Never overwrites: the new place must be free | `vault`, `path`, `to`, `purpose`, `confirm` | changes, can be undone |
| `copy_file` | Copies a file to a new name or folder in the same vault. It stays encrypted the whole time | `vault`, `path`, `to`, `purpose` | changes, can be undone |
| `trash` | Puts a file or folder in the vault's trash. It stays encrypted inside the vault until you empty the trash | `vault`, `path`, `purpose`, `confirm` | changes, can be undone |
| `trash_list` | Shows what's in the trash: each item's id, where it was, when, and which app | `vault` | reads |
| `empty_trash` | Deletes for good: one item, or the whole trash. You approve it yourself, outside the chat | `vault`, `purpose`, `item` (empty: everything) | deletes for good, you approve |
| `recent_changes` | Shows the latest changes: when, which app, why, and whether they were undone | `vault`, `limit` | reads |
| `undo` | Undoes one change, or the latest one. Refuses when the file changed since, so newer work is never lost | `vault`, `purpose`, `change_id` (empty: the latest) | changes, can be undone |
| `versions` | Lists the earlier versions of a file kept by its changes, newest first | `vault`, `path` | reads |
| `restore_version` | Puts back an earlier version of a file. The current contents are kept as a version too | `vault`, `path`, `version_id`, `purpose` | changes, can be undone |

`purpose` is a few words on why. It's kept with the change (or in the read log), so you can see later why the AI did something.

## How unlocking reaches you

When the AI calls `unlock`, Encryptor tries these in order (`ENCRYPTOR_UNLOCK` can pick just one of them, see [settings.md](settings.md#unlocking-and-auto-lock)):

1. **The AI app opens the unlock page for you,** if the app can do that. You type the password there.
2. **A password box** on a Mac, when the AI app runs on your computer. Not on a server.
3. **A link.** The AI shows it to you in the chat, and you open it in your browser. On a computer it's a page on your own computer; on a server it's a page on your server's address.

The link holds a one-time code that only opens the password page. It works once, for 5 minutes, and the password is still typed only on that page. Never type a vault password in the chat.

## When a tool says no

Tools answer in English; the AI tells you in your language.

| The message says | Why | What to do |
|---|---|---|
| "No vault called ..." | The name is wrong, the vault is **Hidden from AI**, or (on a server) this app wasn't given that vault | Check the name with *"Which vaults can you use?"*. On a server, change the app's vaults on the control center (**Choose vaults**) |
| "The vault ... is locked" | It locked by itself, or was never opened | Let the AI ask to unlock it |
| "The unlock page wasn't used in time" | Nobody typed the password within 5 minutes | Ask again |
| "Too many wrong passwords. Try again in ... minutes." | 5 wrong passwords for that vault within 15 minutes | Wait, then try again |
| "Read only for every AI app is on" | The **Safety** switch, or `ENCRYPTOR_READ_ONLY` | Turn it off on the control center, if it isn't fixed in the settings |
| "... is set up as read only" | The vault's mode is **Read only** | Change **The AI may** in the vault's settings |
| "... is open read only" | You ticked **Read only** when unlocking | Lock it and unlock it again without that box |
| "This app may only read ..." | On a server, the app wasn't allowed to change files | Tick **It may change files** for that app on the control center |
| "... already exists. Read it first and pass its version ..." | The AI tried to write over a file it hasn't read | Nothing to do: the AI reads it first, or adds to it |
| "... changed since you read it" | Someone (you, another app, a sync) changed it meanwhile | The AI reads it again first, so your change isn't lost |
| "... already exists there." | A move, copy or new file would land on an existing name | Choose another name, or trash the old one first |
| "... changed since then, so undoing would lose newer work" | The file was changed again after that change | Use `versions` and `restore_version` instead |
| "It's no longer in the trash (the trash was emptied)." | That item was deleted for good | It can't come back |
| "That change was already undone" / "An undo can't be undone" | Undo works once per change, and not on an undo | Make the change again instead |
| "... isn't an empty folder any more" | Undoing a new folder only works while it's empty | Move or trash it instead |
| "'.encryptor' holds Encryptor's own records" | That hidden folder is off limits to the AI | Use the undo, version and trash tools |
| "More than 60 changes in a minute: slowing down." | The brake on fast changes | Wait a moment |
| "Another change to this vault is still running" / "Another program is changing this vault" | Two changes never run at the same time | Try again in a moment |
| "Too long: at most 5000000 characters at a time" | The text is over the write limit | Write it in parts with `append_file` |
| "Deleting for good is switched off for AI apps." | The **Safety** switch is off | Empty the trash yourself on the control center |
| "This can't be approved in the chat." | Deleting for good needs an approval outside the chat, and none was available | Use **Delete for good** on the vault's page in the control center |
| "The user didn't allow it" | You said no, or the question timed out | Nothing was changed |
| "That confirmation code doesn't match this action, was already used, or expired." | A one-time code is for one action, once, for 5 minutes | Ask again; nothing was changed |

## Limits

| What | Limit |
|---|---|
| `read_file` | 50,000 characters at a time by default, 200,000 at most. Longer files are read in parts with `offset` |
| `find` | 100 results by default, 1,000 at most |
| `recent_changes` | 20 changes by default, 200 at most |
| `write_file`, `append_file` | Text only, up to 5,000,000 characters at a time |
| Pictures, PDFs and other binary files | `read_file` doesn't show them as text. You can view or download them on the control center |
| Changes | At most 60 a minute per vault |

**Read-only setups don't get the tools that change files.** When every vault is **Read only** or **Hidden from AI**, the eight tools that change files and `empty_trash` are left out when the AI app starts. If you later set a vault to **Read and change**, restart the AI app to get them back. With **Read only for every AI app** on, the tools stay listed but refuse to change anything.

## Asking first

Every change the AI makes can be undone, so by default the AI doesn't ask before changing a file. If you want it to, set `ENCRYPTOR_ASK_BEFORE` ([settings.md](settings.md#approvals)):

| Value | Asks before |
|---|---|
| `replace` | `write_file` replacing a file that exists |
| `trash` | `trash` |
| `move` | `move` |

You're asked in a Mac box, or in your AI app's own question if it has one. When neither is possible, the AI gets a one-time code and must ask you in the chat. Only when you clearly say yes does it call the tool again with `confirm` set to that code. The code works once, for 5 minutes, for that exact action.

`empty_trash` is different, because it can't be undone. It's never approved in the chat: only in the Mac box, in your AI app's own question, or by you with **Delete for good** on the vault's page in the control center. On Windows or Linux, in an app without its own questions, the AI sends you to the control center.
