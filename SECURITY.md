# Security policy

Encryptor MCP opens encrypted vaults for AI apps. Security reports are very welcome.

## Supported versions

Only the newest release gets security fixes.

## Reporting a problem

Please **don't** open a public issue for a security problem.

1. Go to the **Security** tab of this repository and click **[Report a vulnerability](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/security/advisories/new)**. Only the maintainer sees it.
2. Say:
   - the version (`encryptor-mcp version`, or About on the control center) and how you run it (computer, extension, Docker)
   - what you found, and where in the code if you know
   - the steps to reproduce it
   - what an attacker could do, and what they need first (for example access to the computer, or the passphrase)
3. Never send real passwords, recovery keys, passphrases or vault contents. Use a test vault.

You'll get an answer within a week. Please give time for a fix before talking about it in public.

## What counts

Anything that could reveal a vault password, a vault's keys or decrypted contents to someone who shouldn't have them; let an AI app do more than it was allowed; change a vault in a way Cryptomator can't read; or let someone use the pages without signing in. See [docs/threat-model.md](docs/threat-model.md) for what's in and out of scope.
