# Languages

The pages (unlock, a vault's page, browsing files and the whole control center) come in **20 languages**, and an AI agent can add more with one command.

Your AI app already talks to you in your own language: the tools answer it in English, and the AI explains in yours. So only the pages need translating.

## Which language you see

The pages follow your **browser's language**. If there's no file for it, you see English. To pick one for every browser, add a setting (in your [settings file or environment](settings.md#where-settings-come-from)):

```
ENCRYPTOR_LANGUAGE=pt-BR
```

The next page you open uses it (after a restart if you set it as an environment variable). A code with no file behind it is ignored, and the pages follow the browser again.

| Language | Code | | Language | Code |
|---|---|---|---|---|
| English | `en` | | Russian | `ru` |
| Spanish | `es` | | Ukrainian | `uk` |
| Portuguese (Brazil) | `pt-BR` | | Japanese | `ja` |
| French | `fr` | | Chinese (Simplified) | `zh-CN` |
| German | `de` | | Chinese (Traditional) | `zh-TW` |
| Italian | `it` | | Korean | `ko` |
| Dutch | `nl` | | Hindi | `hi` |
| Polish | `pl` | | Indonesian | `id` |
| Swedish | `sv` | | Vietnamese | `vi` |
| Turkish | `tr` | | Greek | `el` |

The translations were made with AI, not by native speakers. If something reads oddly, please [fix it](#fix-a-translation).

## What stays in English

- **What the tools tell your AI app.** The AI reads it and answers you in your language, so nothing is lost.
- **Your own names:** vault names, folder and file names, and app names (Claude, ChatGPT, Finder) are shown as they are.
- **A few messages that come from deeper inside**, like a health check's findings, some error messages, and the notes after saving a setting. They're plain English sentences, the same ones your AI app sees.
- **Setting names** (`ENCRYPTOR_READ_ONLY=on`), commands and the docs, so they always match each other. To read a docs page in your language, ask your AI app: *"Explain this page in Polish."*

## Add a language with your AI agent

Give an AI coding agent (Claude Code, Codex, Cursor and others) this request, in a copy of the repository:

> *"Add Thai to my Encryptor MCP pages: run `encryptor-mcp translate th`, translate every text in natural Thai, then run `encryptor-mcp translate --check th` until it passes."*

What happens:

1. `encryptor-mcp translate th` makes `th.json` in your config folder's `locales/` (`~/.config/encryptor-mcp/locales/`, in Docker `/data/locales/`). It lists every English text of the pages, with an empty space for each translation.
2. The agent fills them in. Each `{placeholder}` and HTML tag (like `<b>`) stays exactly as in English.
3. `encryptor-mcp translate --check th` makes sure nothing is missing or broken.
4. Restart your AI app (or the server). Browsers set to Thai now see the pages in Thai.

Missing texts show in English, so a half-done file still works. A translation with a broken placeholder or tag is skipped, and that text shows in English. When the project gets new texts, run the command again: it keeps what's translated and adds only the new ones.

In Docker, run the commands inside the container: `docker compose run --rm encryptor encryptor-mcp translate th`.

Right-to-left languages (Arabic, Hebrew, Persian) translate the same way. The page layout itself isn't mirrored yet, so their pages read correctly but are aligned to the left.

## Fix a translation

Your own files in `locales/` win over the ones that come with Encryptor. To fix one text for yourself, run `encryptor-mcp translate de`: it copies the German file into your folder, where you can change any line. Check it with `encryptor-mcp translate --check de`, then restart your AI app (or the server) to see it.

To fix it for everyone, open a pull request that changes `src/encryptor_mcp/locales/<code>.json`, or open an issue with the old and new wording. New languages are welcome the same way.

## Settings

| Setting | Default | What it does |
|---|---|---|
| `ENCRYPTOR_LANGUAGE` | empty (follow the browser) | Show the pages in one language, for example `de` or `zh-TW` |

Your own translation files live in `<config folder>/locales`. The config folder is set with `ENCRYPTOR_CONFIG_DIR` ([settings](settings.md#folders-and-names-environment-only)).
