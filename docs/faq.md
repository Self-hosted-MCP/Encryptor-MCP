# FAQ

**Do I need Cryptomator?** No, but it works alongside it. Encryptor MCP can create vaults itself; Cryptomator opens them, and Encryptor opens Cryptomator's.

**Does my AI see my password?** No. You type it on a page in your browser. No tool takes a password.

**Which AI apps work?** Any app that supports MCP: Claude Desktop, Claude Code, claude.ai, ChatGPT, Cursor, Codex, VS Code, Windsurf, Gemini CLI and more. See [connect-your-ai.md](connect-your-ai.md).

**Can it read old Cryptomator vaults?** Vault format 8 (Cryptomator 1.6 and later), in both cipher modes. Older formats 6 and 7: not yet. Cryptomator itself can upgrade them to format 8.

**Can the AI delete my files?** It can put them in the vault's trash, and you can take them back out. Deleting for good needs your approval outside the chat, and you can switch it off.

**What if I forget the password?** Use the vault's recovery key (44 words) on the vault's settings page. It's the same as Cryptomator's.

**Where do the files go when the AI reads them?** They're decrypted in memory and the text goes to your AI app, like a file you'd paste in. Nothing is written to disk decrypted.

**Can I use it on my phone?** Yes, with the server version: [setup-own-server.md](setup-own-server.md).

**Is it audited?** Not yet. See [threat-model.md](threat-model.md).

**Who made it?** s17sh70x2jfl031ag, open source under the AGPL-3.0. Not made by or affiliated with Cryptomator.
