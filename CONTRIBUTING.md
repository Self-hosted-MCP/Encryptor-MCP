# Contributing

Thank you for helping. Small, focused changes are easiest to review.

1. Read [AGENTS.md](AGENTS.md): the layout and the rules.
2. Set up: install [uv](https://docs.astral.sh/uv/), then `uv sync`.
3. Tests: `uv run pytest -q`. The compatibility tests need a Java runtime (21 or newer; 25 for Cryptomator's current libraries) and either Cryptomator.app or the libraries from `uv run python tests/java/fetch_jars.py .jars` (then `CRYPTOMATOR_MODS=.jars`). Without them those tests are skipped.
4. Keep words plain in anything people read, and never put real vaults, passwords or file contents in issues, tests or commits.

Security problems: see [SECURITY.md](SECURITY.md), not an issue.
