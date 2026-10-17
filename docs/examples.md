# Things to ask

You talk to your AI app in plain words, in your own language. It picks the right tool. Here are ways to ask, grouped by job. Change the vault and file names to yours.

A locked vault opens only when you type its password yourself, on the unlock page or in a Mac password box. So the first time in a chat, the AI asks to unlock, and you say yes there.

> [!TIP]
> If the app doesn't use the vault tools by itself, start with *"Use the Encryptor tools:"*.

<p align="center"><img src="images/chat.png" alt="A chat: you ask to sum up the 2025 receipts; the AI unlocks Taxes 2025, reads them, adds the total to tax-notes.md, then locks the vault" width="640"></p>

## Find and read

- *Which vaults do I have, and which are open?*
- *Open my Taxes vault. I need the 2025 receipts.*
- *What's in the Taxes vault, in the 2025 folder?*
- *Find every file with "invoice" in its name in Taxes.*
- *Read my notes from the March meeting and give me the three decisions.*
- *How big is the contract PDF, and when did it last change?*
- *Read the long journal file in parts and summarise each month.*

The AI reads text files. Pictures, PDFs and other binary files aren't shown to it as text: open those yourself on the control center (**Browse files**).

## Write and add

- *Make a new note called Ideas.md in Notes with these points.*
- *Add today's date and "paid the rent" to the end of my budget log.*
- *Fix the typos in the March notes and save it.*
- *Make a folder called 2026 in Taxes.*
- *Make a copy of the lease letter called "lease letter, draft 2".*

Every change your AI makes keeps what it replaced, and can be undone.

## Tidy and move

- *Move every 2024 receipt into a folder called 2024.*
- *Rename "scan 0012.txt" to "electricity bill March.txt".*
- *Which files in Notes look like duplicates? Don't change anything yet.*
- *Put the old drafts folder in the trash.*

The AI never overwrites when it moves: the new place must be free.

## Undo and earlier versions

- *What did you change in Notes today?*
- *Undo the last change.*
- *Undo the move of the receipts folder.*
- *Which earlier versions of my budget log are there?*
- *Put back the budget log as it was before this morning.*

More: [undo-and-backups.md](undo-and-backups.md).

## Trash

- *What's in the trash of Notes?*
- *Take the drafts folder back out of the trash.*
- *Empty the trash of Notes.* (you approve outside the chat: see [Careful ones](#careful-ones))

## Lock and unlock

- *Unlock Taxes for a quick look.*
- *Lock Taxes now.*
- *Lock everything, I'm done.*
- *How long until Notes locks by itself?*

The AI can lock a vault, but only you can open one. You choose how long it stays open on the unlock page.

## Several vaults

If you have more than one (named, say, *Taxes*, *Notes* and *Health*):

- *Which vaults can you use?*
- *Find "passport" in Taxes and in Notes.*
- *Copy this summary into Notes, not Taxes.*

Vaults set to **Hidden from AI** never show up. More: [vaults-and-apps.md](vaults-and-apps.md).

## Health check and sync conflicts

- *Run a health check on Taxes.*
- *My sync app says there's a conflict in d/AB/CDEF.../name.c9r. Which file is that?* (`decrypt_name`)
- *Where is the contract stored encrypted, so I can find it in my sync app?* (`locate`)
- *Is anything in Notes cut short or swapped since last time?*

The AI only looks. Repairs are yours to make, on the vault's page in the control center (**Health**).

## The control center

- *Open my Encryptor control center.*
- *Where do I change what the AI may do with Health?*
- *How do I change the password of Taxes?*

Creating a vault, changing its password and the recovery key happen only on the control center. The AI can send you there, but never handles them.

## Careful ones

- *Empty the trash of Notes.*
- *Delete the old drafts folder for good.* (the AI puts it in the trash, then asks to empty that one item)

Deleting for good can't be undone. You approve it outside the chat: in a Mac box, in your AI app's own question, or with the **Delete for good** button on the control center. A "yes" typed in the chat is never enough. See [tools.md](tools.md#asking-first).

## Asking well

- **Never paste a vault password or recovery key into the chat.** You type passwords only on the unlock page or in the Mac password box. Recovery keys are only for the control center.
- **Say why.** *"Read the lease to check the deposit"* works better than *"read the lease"*. Your reason is kept as the purpose: you see it on the unlock page, in the record of changes and in the read log.
- **Name the vault** when you have several, unless you've chosen a default vault.
- **Ask for a plan before a big clean-up.** *"Which files would you move? Don't do it yet."* Then say yes.
- **Lock when you're done.** *"Lock everything"* wipes the keys from memory right away. Vaults also lock by themselves after a while.
