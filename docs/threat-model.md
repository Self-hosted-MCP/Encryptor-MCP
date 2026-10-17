# Threat model

What Encryptor MCP protects against, and what it can't. Written plainly so you can decide where to use it.

## What it protects

| Situation | What happens |
|---|---|
| Someone gets the vault folder (a cloud provider, a stolen USB stick, a backup) | They see only Cryptomator's encrypted files. Same as Cryptomator. |
| An AI app (or a prompt injection inside a file) wants a password | No tool takes one; unlocking happens on your own page. |
| An AI app wants more than you allowed | Hidden vaults don't exist for it; read-only vaults refuse changes; on a server each app gets only the vaults you ticked. |
| An AI app makes a bad change | Undo, versions, trash; deleting for good needs your approval outside the chat. |
| Two writers at once, or a file changed elsewhere meanwhile | One writer at a time; replacing needs the version read; nothing is overwritten blindly. |
| A sync app cuts a file between its parts, or files get swapped | The fingerprint list catches it (the format can't). |
| Someone edits or removes read log entries | The chain breaks and the page says so. |
| A web page tries to use your local unlock page (DNS rebinding, cross-site forms) | Refused: host names and form origins are checked. |
| Guessing a vault password on the unlock page | One-second wait per try, a 15-minute pause after five. |
| Forgetting the password | The recovery key (44 words, same as Cryptomator's) sets a new one. |

## What it can't protect

- **Anyone controlling the computer or server while a vault is open** can read memory, and so the keys. Use a computer or server only you control. Vaults lock by themselves to keep that window short.
- **What you let the AI read, the AI's provider sees.** Opening a file for your AI sends its text to that AI. Use read only or hidden for vaults the AI shouldn't see.
- **Metadata:** file sizes, counts and dates are visible in the encrypted folder (true for Cryptomator too).
- **Changing the password doesn't change the vault's master key** (as in Cryptomator). If the master key itself may have leaked, make a new vault and move the files.
- **Deleting both read log files at once** starts a new, empty log; that can't be noticed from the files alone.
- **The Finder mount and the macOS Spotlight or thumbnail caches:** Spotlight indexing is turned off for the mount, but files you open may be cached by macOS like any opened file.
- **A malicious program running as you** on the same computer can do what you can. On a computer, the Finder mount accepts only macOS's own mount agent of your user; the unlock and control center pages are local only.

## Not audited yet

Encryptor MCP has not had an independent security audit. Its encryption follows Cryptomator's published format and is tested against Cryptomator's own code, but treat it as new software: keep backups.
