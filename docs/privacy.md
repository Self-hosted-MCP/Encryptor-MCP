# Privacy

- **No account, no cloud service of ours, no tracking, no analytics.** Encryptor MCP runs on your computer or your server.
- **It talks to the internet only if you turn on the update check** (off by default): once a day it asks GitHub for the newest version number. Nothing about you or your vaults is sent.
- **What it keeps**, in `~/.config/encryptor-mcp` (or `/data` on a server), owner-only:
  - settings you made on the control center (vault names and folders, choices);
  - on a server: connected AI apps, with their login tokens kept only as fingerprints;
  - remembered sign-ins (fingerprints only) and the sign-in log of the last 7 days (time, browser, address; never a passphrase);
  - per vault, the read log and the fingerprint list, both encrypted with a key made from the vault's own key.
- **Inside your vault**, encrypted like your files: the change record, earlier versions and the trash (in a hidden `.encryptor` folder).
- **Never kept anywhere:** vault passwords, the vault's keys (memory only, wiped on lock), recovery keys.
- **Your AI app's provider** sees what your AI reads and writes, like any file you share with it.
