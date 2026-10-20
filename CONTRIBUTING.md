# Contributing

Thanks for wanting to help. Encryptor MCP is free and open source under the [AGPL-3.0](LICENSE). Bug reports, fixes and clearer docs are all welcome. Small, focused changes are the easiest to review.

## Reporting a problem

Click **New issue** on GitHub and pick a form:

| Form | Use it when |
|---|---|
| **Something doesn't work** | You hit a bug or an error message |
| **Question or idea** | You want to know how to do something, or have an idea |
| **Report a security problem, privately** | Someone could misuse Encryptor or reach a vault. Only the maintainer sees it |

Each form asks for what's needed to help you, such as how you run Encryptor and which AI app you use. There's no email contact: the forms and private reporting keep the conversation in one place.

**Leave out vault passwords, recovery keys, your passphrase, file names and anything from your files** before posting. Issues are public. For security problems, don't open an issue: follow [SECURITY.md](SECURITY.md).

## Changing the code

1. Read [AGENTS.md](AGENTS.md). It explains the code and the rules that must never break, such as "the AI never receives a vault password".
2. Install [uv](https://docs.astral.sh/uv/), then the project with its test tools: `uv sync`.
3. Make your change, with a test in `tests/`. Tests use the test vaults in `tests/fixtures/`, with test passwords. Never use a real vault or a real password in a test.
4. Run the tests: `uv run pytest -q`. Everything must pass. The tests also check that every tool is in `docs/tools.md`, that every setting is in `docs/settings.md` and `.env.example`, that every link in the docs works, and that no doc has an em dash.
5. If people will notice the change, update the matching page in `docs/` and add a line to [CHANGELOG.md](CHANGELOG.md).
6. Open a pull request saying what changed and why.

### The compatibility tests

The compatibility tests ([tests/java/RefVault.java](tests/java/RefVault.java)) check that vaults written by Encryptor open in Cryptomator, and the other way round. They need:

- **Java 25 or newer** (a JDK, so `java` can run a `.java` file directly).
- **The reference libraries.** On a Mac with Cryptomator installed, they're found in `/Applications/Cryptomator.app` by themselves. Anywhere else, download them (each file is checked against a pinned fingerprint):

```bash
uv run python tests/java/fetch_jars.py .jars
```

Then run the tests with that folder:

```bash
CRYPTOMATOR_MODS=.jars uv run pytest -q
```

Without Java or the libraries, those tests are skipped, not failed. A change to anything in `src/encryptor_mcp/vault/` or `changes.py` must pass them before it's merged. One recovery key test only runs on a Mac with the Cryptomator app installed.

The **Tests** workflow on GitHub runs everything on macOS, Windows and Linux, for every push to `main` and every pull request.

## Rules

- **Never weaken the safety rules** in [AGENTS.md](AGENTS.md#rules-that-must-never-break). They are the product. A change that touches one needs a very good reason, a test, and a clear note in the pull request.
- No tool may ever take a password, a recovery key or the passphrase.
- Keep the pages free of scripts, and escape every value.
- Don't add new runtime dependencies without a strong reason.

## Releases (maintainers)

1. Set the new version in `pyproject.toml`, `CITATION.cff` and `.claude-plugin/plugin.json` (both the `version` and the `@vX.Y.Z` in its install line). Move the notes in [CHANGELOG.md](CHANGELOG.md) under that version, with the date.
2. Run the tests (with the reference libraries) and wait for the **Tests** workflow on GitHub to pass.
3. Push to `main`, tag it `vX.Y.Z`, and publish a GitHub Release with the changelog notes.

Publishing the release starts two workflows. **Docker image** builds the ready-made image for amd64 and arm64 and publishes it as `ghcr.io/self-hosted-mcp/encryptor-mcp` (tags: the version, major.minor and `latest`). The **Claude Desktop extension** workflow builds `encryptor-mcp-<version>.mcpb`, checks it with Anthropic's validator, and attaches it to the release, also as `encryptor-mcp.mcpb` so one link always gets the newest. Nothing reaches the image or the extension before a release is published.

## Writing docs

The docs are for people who have never used a terminal.

- Short sentences (8 to 20 words), everyday words, "you". Explain any technical word the first time.
- Headings in sentence case, phrased the way a reader would ask ("If something goes wrong").
- One command per code block, and show what the reader should see when it works.
- Button and page names in **bold**, exactly as on the page. Example questions for the AI in *italics*. Commands, settings and file names in `code`.
- No em dashes. Use colons, commas or brackets.
- Never write that something was tested unless it was. Say "not supported" with the reason.
- Where it matters: "Works with Cryptomator vaults. Not made by or affiliated with Cryptomator."
- Never say Encryptor is tested or checked against Cryptomator (its code or libraries), in docs, pages, images, release notes or posts. Say what it does: it keeps vaults in Cryptomator's format.

## Credit and license

By contributing, you agree that your work is shared under the [AGPL-3.0](LICENSE), the same license as the rest of the project. Keep the original credit ([LICENSE](LICENSE), [NOTICE](NOTICE), `CITATION.cff`, the About page) and add yourself to the changelog entry if you like.
