# Roadmap

What might come next. Nothing here is promised or has a date. If you want one of them, say so with the [question or idea form](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/issues/new?template=question.yml), or help build it ([CONTRIBUTING.md](../CONTRIBUTING.md)).

## Wanted

- **Older vaults (format 7, maybe 6).** Format 7 (Cryptomator 1.5) stores files and names much like format 8, so reading it looks realistic. Format 6 keeps long names in a different way and would be more work. Until then, a current Cryptomator can upgrade an old vault to format 8, and it works here after that.
- **Translations of the pages.** The control center and unlock pages are English only for now. Your AI already answers you in your own language.
- **A ready-made Docker image**, so a server doesn't have to build it first. Today `docker compose up -d --build` builds it from the source.
- **A background service on a computer**, so the control center has a fixed address you can bookmark. Today it runs only while an AI app runs Encryptor, on a new address each time.
- **A password box on Windows and Linux**, like the one on a Mac, for AI apps that can't open the unlock page. Today those get a link to open instead.

## Maybe

- **Cryptomator Hub vaults**, where the key comes from a Hub server instead of a password. It would need a safe way to sign in to Hub without the AI ever touching the key.
- **Phones without a server.** Today a phone reaches your vaults through the server version only.

## Not planned

- **A hosted service run by us.** This project is for running your own copy. Holding other people's vault keys is a responsibility we don't want, and you shouldn't have to trust us with it.
- **Storing vault passwords.** You type the password each time a vault opens. A stored password would let anyone with access to that computer or server open your vaults without you.
- **Guides for hosting companies.** While a vault is open, its keys would sit in the hosting company's memory, and your vault folders would have to be on its disks. Run it on your computer, or on a server you control ([setup-own-server.md](setup-own-server.md)).
- **Add-ons with access to the keys.** Anything that can reach an open vault's keys can read every file. Keeping that door closed is simpler and safer than checking every add-on.
