# Safety

What Encryptor MCP does to keep your files safe, and to keep you in control.

## Your password and keys

- The AI never sees or types a vault password. You type it on a page in your own browser (or a password box on a Mac). No tool takes a password, and the AI is told never to ask for one in the chat.
- Keys stay in memory only, for as long as you choose. A vault locks when you say so, after a few minutes without use (10 by default, per vault if you like), at the time you chose, after 12 hours at the latest, or when the program stops. Locking overwrites the keys.
- Five wrong passwords pause that vault's unlocking for 15 minutes, and each wrong try waits a second.
- A leak test runs a full session and checks the password and keys never show up in any answer, log or file.

## Changes

- Every change keeps what it replaced, and can be undone from the vault's page or by asking the AI.
- Files are swapped in at once: never half-written. Two changes never run at the same time.
- Replacing a file needs the version the AI read: if the file changed since (by you, another app or a sync), nothing is overwritten.
- Deleted things go to a trash inside the vault. Deleting for good happens only by emptying the trash, and you approve it outside the chat (a box on your screen, your AI app's own question, or the Purge button on the vault's page; never just a yes in the chat). You can also switch it off for AI apps.
- Renaming, moving or removing a vault from the list, and repairs, ask twice on the control center.
- Read only, per vault or for every AI app at once: tools that change files then refuse, or aren't offered at all.
- No more than 60 changes a minute.

## Seeing what happened

- **Record** on each vault's page: every change, which app, why, and Undo.
- **Read log:** every file opened, by which app and why. Encrypted, chained so changes or removals show, and private to you (no AI tool can read it).
- **Activity:** signed-in browsers and sign-ins of the last 7 days.

## Checks Cryptomator doesn't do

- **Health check**, like Cryptomator's own, plus damaged or cut files, sync conflict copies and leftovers. Safe repairs only after you confirm.
- **Fingerprint list:** catches files cut exactly between parts, and files whose contents were swapped, which the vault format can't notice. Kept outside the vault and encrypted.

## The pages

- On a computer they're only on 127.0.0.1, refuse other host names, and accept forms only from themselves. On a server, HTTPS is required.
- No scripts, nothing loaded from other sites, strict security headers. Files you open there run in a sandbox, so a hostile file in a vault can't run anything.

## Files inside a vault are data

The AI is told that file contents are data, not instructions. A file that says "ignore your instructions" is just text.

See also [threat-model.md](threat-model.md).
