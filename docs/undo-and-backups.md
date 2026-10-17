# Undo and backups

Every change your AI makes is written down, keeps what it replaced, and can be undone. The same goes for changes made in Finder (**Show in Finder**) and for **Undo** and **Restore** on the control center. A few things can't be undone: see [What can't be undone](#what-cant-be-undone).

## The record of changes

<p align="center"><img src="images/undo.png" alt="Every change your AI makes can be undone: the record of changes, each with an Undo button" width="640"></p>

Each change is saved with: when, which app, why (the purpose the AI gave), what it did, and how to undo it.

- Ask the AI: *"What did you change in Notes today?"* (the `recent_changes` tool, up to 200 changes).
- Or open the vault's page on the control center: the **Record** card shows the last 15 changes, each with an **Undo** button.

The record lives inside the vault itself, encrypted like every other file. So it syncs with the vault, and nobody without the password can read it. See [the hidden .encryptor folder](#the-hidden-encryptor-folder).

Changes made outside Encryptor (in Cryptomator, or on another device) aren't in the record.

## Undo

Ask *"undo that"*, or press **Undo** on the vault's page. Without saying which, the AI undoes the latest change.

| The change was | Undo does this |
|---|---|
| A new file, or a copy | Puts that file in the trash |
| A file replaced, added to, or put back to a version | Puts back the contents from before |
| A new folder | Removes it, if it's still empty |
| A move or rename | Moves it back |
| Something put in the trash | Takes it back out, to where it was |

When undo refuses, it says why, and nothing is changed:

- **The file changed again since.** Undoing would lose that newer work. Use the earlier versions instead ([below](#earlier-versions)).
- **The folder isn't empty any more.** Move or trash it instead.
- **The trash was emptied.** That item is gone for good.
- **Something else now has that name.** Move it out of the way first.
- **It was already undone,** or it's an undo itself. An undo can't be undone: make the change again instead.
- **It was deleting for good.** That can't be undone.

Undo looks back over the last 500 changes.

## Earlier versions

Every time a file is replaced or added to, the old contents are kept as a version. Ask:

- *"Which earlier versions of my budget log are there?"* (`versions`, newest first)
- *"Put back the one from before this morning."* (`restore_version`)

Putting back a version keeps the current contents as a version too, so you can go back and forth. It's a change like any other: it's in the record and can be undone.

## The trash

Putting something in the trash doesn't delete it. **Trash** moves it into the vault's own trash, where it stays encrypted.

- *"What's in the trash of Notes?"* (`trash_list`), or the **Trash** card on the vault's page.
- *"Take the drafts folder back out of the trash."* (`undo`), or **Restore** on the vault's page.

### Deleting for good

Emptying the trash is the only way anything is deleted for good, and it can't be undone.

- **On the control center:** on the vault's page, open **Delete the trash for good**, tick the box, and press **Delete for good**. This empties the whole trash.
- **By asking the AI** (`empty_trash`): one item or the whole trash. You approve it yourself outside the chat, in a Mac box or your AI app's own question, never with a "yes" in the chat. If neither is possible, the AI sends you to the control center.

When you approve it through the AI, anything put in the trash after you approved stays there. **Delete for good** on the control center empties whatever is in the trash at that moment. You can stop AI apps from asking at all: **Settings**, **Safety**, untick **AI apps may ask to delete the trash for good**.

## The hidden .encryptor folder

The record, the earlier versions and the trash live in a hidden folder called `.encryptor`, at the top of each vault. Like everything in a vault, it's encrypted.

- **The AI can't open it directly.** It uses the record, version and trash tools instead.
- **Cryptomator shows it.** When you open the vault in Cryptomator, you'll see a `.encryptor` folder. Leave it there if you want undo, versions and the trash to keep working.
- **It grows.** The trash shrinks when you empty it. Earlier versions and the record are never removed by Encryptor, so a vault with many changes slowly gets bigger.
- **To start fresh,** delete the `.encryptor` folder in Cryptomator. That throws away every earlier version, the record, and everything in the trash, for good.

It's made the first time something changes through Encryptor. A vault that's only ever read never gets one.

## At a glance

| To | Ask the AI | On the control center (the vault's page) |
|---|---|---|
| See what changed | *"What did you change today?"* | **Record** |
| Undo a change | *"Undo the last change."* | **Undo** |
| See earlier versions | *"Which versions of this file are there?"* | |
| Put one back | *"Put back the version from yesterday."* | |
| See the trash | *"What's in the trash?"* | **Trash** |
| Take something out | *"Take it back out of the trash."* | **Restore** |
| Delete for good | *"Empty the trash."* (you approve outside the chat) | **Delete the trash for good**, tick the box, **Delete for good** |

## What can't be undone

- **Emptying the trash.** Anything deleted for good is gone. That's why it always asks you first, outside the chat.
- **An undo.** Undoing an undo isn't possible: make the change again instead.
- **An undo that would lose newer work.** If the file changed after that change, undo refuses instead of overwriting the newer version. Put back an earlier version ([Earlier versions](#earlier-versions)).
- **Repairs from the health check.** They fix the vault's structure on the control center, and they aren't in the record. One of them deletes a leftover temporary file from an interrupted save.
- **Password and recovery key changes,** creating a vault, and removing one from the list. They don't change your files, so there's nothing in the record to undo.
- **Everything in the `.encryptor` folder,** if you delete it.
- **Changes made outside Encryptor:** in Cryptomator, on another device, or by a sync app. They aren't in the record, so there's nothing to undo. If Encryptor later replaces such a file, the version it keeps does include them.
- **A vault whose password and recovery key are both lost.** Nobody can open it, not Encryptor, not Cryptomator.

## Backing up your vaults

A vault is a normal Cryptomator folder of encrypted files. To back it up, copy the whole vault folder, the one that holds `vault.cryptomator`, somewhere else: an external drive, another cloud, a backup app.

- **The copy stays encrypted,** so it's safe wherever you keep it. It includes the `.encryptor` folder, so your record, versions and trash come along.
- **Copy it while the vault is locked,** or at least while nothing is changing it, so the copy is whole.
- **A synced folder isn't a backup.** If a file is deleted or broken in one place, the sync copies that everywhere. Keep at least one copy that doesn't sync.
- **To use a backup,** copy the folder back and add it on the control center (**Settings**, **Add a vault**). It opens with the password it had when you copied it.
- **Keep the recovery key safe,** apart from the backup: on paper or in a password manager. It opens the vault if you forget the password, in Encryptor or in Cryptomator. Encryptor doesn't keep it anywhere.

Your config folder (`~/.config/encryptor-mcp`) holds no files from your vaults: only your choices, plus each vault's fingerprints and read log (both encrypted). If you lose it, add your vaults again; only the read logs and fingerprints start over. See [settings.md](settings.md#files-in-your-config-folder).
