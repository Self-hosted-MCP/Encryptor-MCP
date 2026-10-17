# Threat model

What Encryptor MCP protects against, and what it can't, so you can decide where to use it. The everyday rules are in [safety.md](safety.md).

## What it protects

| Situation | What happens |
|---|---|
| Someone gets the vault folder (a cloud provider, a stolen USB stick, a backup) | They see only Cryptomator's encrypted files. Same as Cryptomator. |
| An AI app (or a prompt injection inside a file) wants a password | No tool takes one; unlocking happens on your own page or in a box on your screen. |
| An AI app wants more than you allowed | Hidden vaults don't exist for it; read-only vaults refuse changes; on a server each app gets only the vaults you ticked. |
| An AI app makes a bad change | Undo, versions, trash; deleting for good needs your approval outside the chat. |
| Two writers at once on one computer, or a file changed elsewhere meanwhile | One writer at a time (a lock file); replacing needs the version read; nothing is overwritten blindly. |
| A sync app cuts a file between its parts, or files get swapped | The fingerprint list catches it (the format can't). |
| Someone edits or removes read log entries | The chain breaks and the page says so. |
| A web page tries to use your local pages (DNS rebinding, cross-site forms) | Refused: host names and form origins are checked. |
| Guessing a vault password | A one-second wait per wrong try on the unlock page, and a 15-minute pause for that vault after five. |
| Guessing the server passphrase from one address | Five wrong tries pause that address for 15 minutes, so a stranger can't lock you out from elsewhere. |
| Guessing the server passphrase from many addresses | Fifty wrong tries from anywhere pause every sign-in for 15 minutes. The counters are in memory and clear on a restart. |
| An AI app names itself "You" to look like you | Any name starting with "You" is shown as "An AI app called You...". |
| Strangers filling the server's app list (registration is open, as the MCP login needs) | At most 50 apps are kept, the oldest go first, and ones that never logged in are forgotten after an hour. Registering gives nothing: each app still needs your passphrase. |
| Forgetting the password | The recovery key (44 words, same as Cryptomator's) sets a new one. |

## What it can't protect

| Situation | Why, and what to do |
|---|---|
| Anyone controlling the computer or server while a vault is open | They can read memory, and so the keys. Use a computer or server only you control. Vaults lock by themselves to keep that window short. |
| What you let the AI read | Opening a file for your AI sends its text to that AI's provider. Use **Read only** or **Hidden from AI** for vaults the AI shouldn't see. |
| Metadata | File sizes, counts and dates are visible in the encrypted folder (true for Cryptomator too). |
| A leaked master key | Changing the password doesn't change the vault's master key (as in Cryptomator). If the master key itself may have leaked, make a new vault and move the files. |
| Deleting both read log files at once | That starts a new, empty log, which can't be noticed from the files alone. |
| Rolling back the read log | Putting back an older copy of both its files at once isn't noticed (same as deleting both). |
| macOS caches from the Finder mount | Spotlight indexing and Quick Look thumbnails are turned off for the mount, but apps you open files with may keep their own copies, like with any opened file. |
| Files you download from the control center | They're saved decrypted, where your browser puts downloads. Delete them when you're done. |
| Two computers changing the same synced vault at once | Each computer has its own lock, fingerprints and read log; they don't coordinate. |
| A malicious program running as you on the same computer | It can do what you can. On a computer, the Finder mount accepts only programs of your own Mac user; the unlock and control center pages are local only. |
| The 127.0.0.1 sign-in cookie | Browsers send a cookie for 127.0.0.1 to every port on 127.0.0.1, so another web page served on your computer could see it if you open that page. That needs a program already running as you, which could read Encryptor's own files anyway. The cookie lasts at most 12 hours and ends when you sign out or close the browser. |
| Someone who keeps your server's sign-in paused | Fifty wrong tries from anywhere pause every sign-in for 15 minutes. They still can't get in. A private address (Tailscale) or a firewall rule helps. |

## Not audited yet

Encryptor MCP has not had an independent security audit. Its encryption follows Cryptomator's published vault format, but treat it as new software: keep backups.
