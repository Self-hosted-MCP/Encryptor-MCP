# Security policy

Encryptor MCP opens encrypted Cryptomator vaults for AI apps. It holds a vault's keys while the vault is open, so security reports are very welcome.

Works with Cryptomator vaults. Not made by or affiliated with Cryptomator. Problems in Cryptomator itself go to the Cryptomator project.

## Supported versions

Only the newest release gets security fixes. Updating is the fix. See [docs/updates.md](docs/updates.md).

| Version | Security fixes |
|---|---|
| 0.1.x (the latest release, [see Releases](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/releases/latest)) | Yes |
| Anything older | No, please update |

## Reporting a problem

Please **don't** open a public issue, discussion or pull request for a security problem.

1. Go to the **Security** tab of this repository and click **[Report a vulnerability](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/security/advisories/new)**. Only the maintainer sees it.
2. Tell me what's in the next section.
3. Never send real vault passwords, recovery keys, passphrases, login keys or vault contents. Use a test vault: make one in Cryptomator, or on the control center.

There's no email contact. Use private reporting.

## What to include

- The version (`encryptor-mcp version`, or **About** on the control center) and how you run it (computer, Claude Desktop extension, Docker, own server).
- Your operating system and your AI app, if it matters.
- What you found, and which part of the code it's in, if you know.
- The steps to reproduce it.
- What an attacker could do with it, and what they need first (for example access to the computer, the passphrase, or a file planted in a vault).

## What happens next

| When | What |
|---|---|
| Within 3 days | You get a first answer saying the report arrived |
| Within 10 days | I confirm the problem (or explain why it isn't one) and agree on a plan |
| Usually within 30 days | A fixed release is published |
| After the release | The advisory is published, with a CVE when it's useful |

This is a project run in spare time, so a date can slip. If it does, you'll hear why. Please keep the problem private until the fixed release is out, or until 90 days have passed, whichever comes first.

## Credit

If you'd like, you're named in the published advisory and in [CHANGELOG.md](CHANGELOG.md). Tell me the name or GitHub account to use, or say you'd rather stay anonymous. There's no paid bug bounty.

## Testing in good faith

If you follow this policy, I won't take any action against you for your research. Please:

- test only on your own vaults and your own computer or server, or ones you have permission to test
- never open, read or change other people's vaults
- stop and report as soon as you see someone else's data
- don't run denial-of-service tests against someone else's server

## In scope

- Anything that could reveal a vault password, a vault's keys, a recovery key or decrypted contents to someone who shouldn't have them (tool answers, pages, error messages, logs, files on disk).
- Any way for an AI app to get a password through a tool, or to unlock a vault without you typing the password.
- Any way for an AI app to do more than it was allowed: see a **Hidden from AI** vault, change a **Read only** vault, reach a vault it wasn't given on a server, or change files when read only for every AI app is on.
- Any way to delete for good without your approval outside the chat, or to reuse an approval or a one-time code.
- Changes that don't land in the record, or an undo that doesn't put back what was there.
- A change that leaves a vault Cryptomator can't read, or damages files.
- Ways to use the control center, the unlock page, a vault's page or the Finder mount without signing in, or from another website or another user on the computer.
- Ways around the passphrase lockout, or to change the read log or fingerprint list without it showing.
- Ways for a file inside a vault to make Encryptor itself do something (not the AI model, which is covered by [docs/safety.md](docs/safety.md)).

## Out of scope

- An AI model following instructions hidden in a file. That's prompt injection, a known limit of today's AI models. Encryptor's defences are in [docs/safety.md](docs/safety.md), and improvements to them are welcome as normal issues.
- A user asking the AI to do something harmful to their own vaults, after the approvals.
- Weak passwords or passphrases chosen by a user, or a settings file shared by its owner.
- What's listed under [What it can't protect](docs/threat-model.md#what-it-cant-protect), such as someone who already controls your computer or server while a vault is open.
- Problems in Cryptomator, your sync app, your hosting company or your AI app. Please report those to them.
- Problems in a dependency that this project doesn't use in a harmful way.
- Missing security headers or reports from automated scanners without a real attack that works.

## Keeping your own setup safe

- Update when a new release comes out.
- Use strong vault passwords, and keep each vault's recovery key somewhere safe and offline.
- On a server, use a passphrase nobody can guess. Eight characters is the minimum; more is better on a server anyone can reach.
- Start with vaults **Read only**, hide the ones the AI doesn't need, and lock vaults when you're done.
- On a server, give each AI app only the vaults it needs, and check **Connected AI apps** and **Activity** on the control center now and then.
- Keep backups of your vaults.
- More in [docs/safety.md](docs/safety.md) and [docs/privacy.md](docs/privacy.md).
