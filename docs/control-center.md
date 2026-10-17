# The control center

The control center is your own page for your vaults, in your browser. Here you unlock and lock vaults, see and undo what changed, empty the trash and choose settings. Your AI apps never see it.

It looks like a set of index cards: one card per vault. It's light by default, with a **Dark** switch at the top right, and it works on a phone.

## Opening it

<details open><summary><b>On a computer</b></summary>

The control center runs on your own computer only (the address `127.0.0.1`), on a random port. It's there only while an AI app that uses Encryptor is running: closing the app closes it too.

- **Ask your AI app:** *"Open my Encryptor control center."* It opens in your browser, already signed in. The AI never sees the link.
- **Or unlock a vault yourself.** If you open an old control center tab, you see **Open your control center**, with your vaults listed. Press **Unlock** next to one and type its password: that signs you in too. Vaults set to **Hidden from AI** aren't listed there.
- **Or from a vault's page.** After you unlock a vault, its page has an **All vaults** link at the top.

On a computer, a sign-in lasts until the AI app closes, 12 hours at most.

</details>

<details><summary><b>On a server</b></summary>

Open your server's address (for example `https://vault.example.com`) and type your **Passphrase**. Tick **Remember this browser for 90 days** to stay signed in; otherwise a sign-in lasts 12 hours at most, and ends when the server restarts.

Five wrong passphrases from one address within 15 minutes pause sign-in from there: "Too many wrong tries. Wait 15 minutes."

</details>

At the top of every page: **Vaults**, **Settings**, **Activity**, **About** and **Sign out**.

## Vaults

The home page, **Your vaults**, lists every vault:

- **Locked**, or open and **Lent to** an app, with a **Due** stamp: the time it locks at the latest.
- A note when the AI may only read it, when it's hidden from the AI, and which one is the **default**.
- **Unlock** or **Lock**, **Open** (the vault's page, when it's open) and **Settings** (that vault's settings).
- **Add a vault**, and **Lock all** when anything is open.

On a server, **Connected AI apps** is here too: each app that connected, the vaults it may ask for, and whether it may change files. **Choose vaults** changes that; **Disconnect** signs the app out, and it has to connect again with your passphrase. More: [vaults-and-apps.md](vaults-and-apps.md#each-ai-app-on-a-server).

## The unlock page

You see it when an AI app asks to open a vault, or when you press **Unlock** yourself.

<p align="center"><img src="images/unlock.png" alt="The unlock page" width="360"></p>

- **Asked by** and **Why**: which app is asking, and its reason. Only continue if you asked your AI app for this just now.
- **Vault password.** It stays on this page; the AI never sees it.
- **Keep it open:** **15 minutes**, **1 hour**, **Until I lock it** (chosen at first) or **Until the AI app closes**. That last one is on a computer only, because closing the app ends Encryptor there. Whatever you choose, a vault never stays open longer than 12 hours (`ENCRYPTOR_MAX_HOURS`).
- **Read only: the AI can look, not change.** Tick it for a quick look.

Without use, the vault also locks by itself after a while (10 minutes unless you change it). Each wrong password waits 1 second, and 5 wrong ones within 15 minutes pause that vault.

## A vault's page

<p align="center"><img src="images/vault.png" alt="A vault's page" width="360"></p>

The top card shows when it's **Due back**, which app it's **Lent to**, its **Access** (read only or read and change), how long it's **Kept open**, and after how long **Without use** it locks.

- **Browse files:** folders and files, decrypted only in memory. Pictures (PNG, JPEG, GIF, WebP) and text files open in the browser. Everything else, PDFs included, has a **Download** button only. A download is saved decrypted on your disk, so put it away when you're done.
- **Show in Finder** (Mac only): the open vault appears in Finder under Locations, like a drive. **Remove from Finder** takes it away. It goes by itself when the vault locks.
- **Lock now:** locks it and wipes the keys from memory.

Further down:

- **Record:** the last 15 changes, with which app made them and why. **Undo** puts a change back. Changes made in Finder are here too.
- **Trash:** what was put in the trash, with **Restore**. **Delete the trash for good** opens a box to tick (**Delete ... for good. This can't be undone.**) and the **Delete for good** button.
- **Read log:** which files were opened, by which app or by you, and why. Private to you, and checked for tampering. Your AI apps can't see it.
- **Health:** **Check health** checks every folder, long name and file is whole, like Cryptomator's own health check, and spots files cut short or swapped. When safe repairs exist, **Repair ... safely** shows what it will do, then asks **Yes, repair ...**. Nothing is deleted except leftover temporary files.

When the vault is open read only, there's no **Undo**, **Restore**, **Delete for good** or repair.

More: [undo-and-backups.md](undo-and-backups.md).

## Settings

| Section | What you do there |
|---|---|
| **Vaults** | Every vault, with a **Settings** button for its own page |
| **Add a vault** | A **Name**, the **Vault folder** (the one that holds `vault.cryptomator`) and what **The AI may** do. Nothing is copied or moved. Press **Add vault** |
| **Create a new vault** | A **Name**, **Where** to make it, a **New password** (twice, 8 or more characters) and what **The AI may** do. Press **Create vault** |
| **Auto-lock** | How long a vault may sit unused before it locks, for all vaults: 5, 10, 15, 30 or 60 minutes |
| **Safety** | **Read only for every AI app**, and **AI apps may ask to delete the trash for good (you still approve each time)** |
| **Connect an AI app** | On a server only: the address to add to your AI app |

After **Create vault**, you see its **recovery key**: 44 words, shown once. Write them down or keep them in a password manager, then press **I've saved them**. They work in Cryptomator too.

## A vault's settings

Press **Settings** next to a vault.

- **The AI may:** **Read and change**, **Read only** or **Hidden from AI**. Hidden vaults never show to the AI; you can still open them here.
- **Default vault:** the AI uses it when you don't name one.
- **Auto-lock:** this vault's own time, or **Same as all vaults**.
- **Password:** your **Current password**, then the **New password** twice, and **Change password**. Cryptomator and your other devices use the new one right away. The files aren't re-encrypted, so it's quick.
- **Recovery key:** type the password and press **Show**. **Forgot the password?** lets you type the **Recovery key (44 words)** and **Set the new password**.
- **Name and folder:** **Rename**, or **Change** the folder it points at. Both lock the vault first if it's open.
- **Remove:** **Remove from the list**. The vault and its files stay where they are, and AI apps can no longer ask for it.

Renaming, changing the folder and removing ask twice: a page shows what will happen, with **Yes, rename**, **Yes, change folder** or **Yes, remove it**, and **Cancel**.

Wrong passwords here count towards the same pause as unlocking.

## Activity

Private to you. Your AI apps can't see this page.

- **Signed-in browsers:** each browser signed in to the control center, since when and when last seen. **Sign out** one, or **Sign out every other browser**.
- **Sign-ins, last 7 days:** the last 50 sign-ins and refused tries on this page: when, how, which browser and, on a server, from which address. Passphrases are never written down.

## About

- Your **Version** and the **License** (AGPL-3.0).
- **Check GitHub for a new version once a day (only the version number is asked)**, off by default, with **Save** and **Check now**. More: [updates.md](updates.md).
- **Help:** links to the source code, to report a problem or ask a question, and to report a security problem privately.

Works with Cryptomator vaults. Not made by or affiliated with Cryptomator.
