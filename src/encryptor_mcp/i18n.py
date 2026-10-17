# SPDX-License-Identifier: AGPL-3.0-only
"""Languages for the pages (unlock, vault, browse, control center). Tool answers stay in English: the AI app reads
them and talks to the person in their own language.

Every text a person sees on a page is written in English inside _("...") (or N_("...") where it's stored first and
translated later). A language is a JSON file, locales/<code>.json, mapping each English text to its translation.
Texts may hold {placeholders} and a few HTML tags; a translation keeps both exactly. Missing texts fall back to
English, so a half-done language still works. `python -m encryptor_mcp.i18n <code>` makes or updates a file for an
AI agent (or a person) to fill in, and `python -m encryptor_mcp.i18n --check <code>` checks it.
"""

from __future__ import annotations

import ast
import contextvars
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE_LOCALES = HERE / "locales"
SOURCES = [HERE / "pages.py", HERE / "web.py"]   # the files whose _("...") texts people see

# The languages that ship with Encryptor, by their own name. Others can be added with the command above.
LANGUAGES = {
    "en": "English", "es": "Español", "pt-BR": "Português (Brasil)", "fr": "Français", "de": "Deutsch",
    "it": "Italiano", "nl": "Nederlands", "pl": "Polski", "sv": "Svenska", "tr": "Türkçe", "ru": "Русский",
    "uk": "Українська", "ja": "日本語", "zh-CN": "简体中文", "zh-TW": "繁體中文", "ko": "한국어", "hi": "हिन्दी",
    "id": "Bahasa Indonesia", "vi": "Tiếng Việt", "el": "Ελληνικά",
}

LANG: contextvars.ContextVar[str] = contextvars.ContextVar("lang", default="en")
_catalogs: dict[str, dict[str, str]] = {}
PLACEHOLDER = re.compile(r"\{(\w+)\}")
TAG = re.compile(r"</?[a-z][^>]*>")
CODE = re.compile(r"[a-z]{2,3}(-[A-Za-z]{2,4})?")


def user_locales() -> Path:
    """Your own translation files: <config folder>/locales. They win over the ones that ship with Encryptor."""
    config = Path(os.environ.get("ENCRYPTOR_CONFIG_DIR") or Path.home() / ".config" / "encryptor-mcp")
    return config.expanduser() / "locales"


def catalog(code: str) -> dict[str, str]:
    if code == "en":
        return {}
    if code not in _catalogs:
        found = {}
        for folder in (PACKAGE_LOCALES, user_locales()):   # a user's own file wins
            path = folder / f"{code}.json"
            if path.is_file():
                try:
                    found.update({k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items()
                                  if isinstance(v, str) and v.strip() and not problems(k, v)})
                except (OSError, ValueError, AttributeError):
                    pass
        _catalogs[code] = found
    return _catalogs[code]


def available() -> list[str]:
    codes = {"en"}
    for folder in (PACKAGE_LOCALES, user_locales()):
        if folder.is_dir():
            codes |= {p.stem for p in folder.glob("*.json") if CODE.fullmatch(p.stem)}
    return sorted(codes)


def _(text: str, **values) -> str:
    """The text in the page's language, with {placeholders} filled in. A broken translation falls back to English."""
    translated = catalog(LANG.get()).get(text, text)
    if not values:
        return translated
    try:
        return translated.format(**values)
    except (KeyError, IndexError, ValueError):
        return text.format(**values)


def N_(text: str) -> str:
    """Marks a text for translation without translating it yet (for lists defined before a page is drawn)."""
    return text


def pick(accept_language: str = "", forced: str = "") -> str:
    """The best language for a request: ENCRYPTOR_LANGUAGE if set, else the browser's preferences, else English."""
    codes = available()
    lower = {c.lower(): c for c in codes}

    def match(tag: str) -> str | None:
        tag = tag.strip().lower().replace("_", "-")
        if not tag:
            return None
        if tag in lower:
            return lower[tag]
        if tag.startswith("zh"):   # Chinese: traditional for Taiwan, Hong Kong, Macau and "Hant"
            return lower.get("zh-tw" if any(x in tag for x in ("tw", "hk", "mo", "hant")) else "zh-cn")
        base = tag.split("-")[0]
        if base in lower:
            return lower[base]
        return next((c for low, c in lower.items() if low.split("-")[0] == base), None)

    if forced and match(forced):
        return match(forced)
    wanted = []
    for i, part in enumerate(accept_language.split(",")[:30]):
        tag, _sep, q = part.strip().partition(";q=")
        try:
            wanted.append((float(q or 1), -i, tag))
        except ValueError:
            continue
    for q, _i, tag in sorted(wanted, reverse=True):
        found = match(tag) if q > 0 else None
        if found:
            return found
    return "en"


# ---------------------------------------------------------------- for making and checking a language file

def source_texts(files: list[Path] | None = None) -> list[str]:
    """Every English text inside _("...") or N_("...") in the given source files, in order of appearance."""
    texts = []
    for path in files or SOURCES:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("_", "N_")
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                if node.args[0].value not in texts:
                    texts.append(node.args[0].value)
    return texts


def problems(english: str, translated: str) -> list[str]:
    """What's wrong with one translation: placeholders or HTML tags that don't match the English text."""
    issues = []
    if sorted(PLACEHOLDER.findall(english)) != sorted(PLACEHOLDER.findall(translated)):
        issues.append("the {placeholders} must be exactly the same as in English")
    if sorted(TAG.findall(english)) != sorted(TAG.findall(translated)):
        issues.append("the HTML tags must be exactly the same as in English")
    if "<script" in translated.lower() or "javascript:" in translated.lower():
        issues.append("scripts aren't allowed")
    try:
        translated.format(**{name: "x" for name in PLACEHOLDER.findall(english)})
    except (KeyError, IndexError, ValueError):
        issues.append("unmatched { or } (write {{ or }} for a literal brace)")
    return issues


def translate(args: list[str]) -> None:
    """Writes <config folder>/locales/<code>.json with every English page text as a key; filled-in values are kept,
    new texts get an empty value. --check reports empty values and broken placeholders or tags."""
    check = "--check" in args
    codes = [a for a in args if not a.startswith("--")]
    if len(codes) != 1 or not CODE.fullmatch(codes[0]):
        sys.exit("Usage: python -m encryptor_mcp.i18n <code>   or   python -m encryptor_mcp.i18n --check <code>"
                 "   (codes like ko, pt-BR, zh-TW)")
    code = codes[0]
    texts = source_texts()
    path = user_locales() / f"{code}.json"
    existing: dict = {}
    for source in (PACKAGE_LOCALES / f"{code}.json", path):   # start from the shipped file, then your own changes
        if source.is_file():
            existing.update(json.loads(source.read_text(encoding="utf-8")))
    if check:
        empty = [t for t in texts if not str(existing.get(t, "")).strip()]
        broken = [(t, p) for t in texts if str(existing.get(t, "")).strip() for p in problems(t, existing[t])]
        print(f"{code}: {len(texts) - len(empty)} of {len(texts)} texts translated.")
        for t, p in broken:
            print(f"  FIX  {t[:70]!r}: {p}")
        for t in empty[:20]:
            print(f"  TODO {t[:70]!r}")
        if broken or empty:
            sys.exit(f"{len(broken)} to fix, {len(empty)} still to translate.")
        print("All texts are translated and look right.")
        return
    data = {t: existing.get(t, "") for t in texts}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    todo = sum(1 for v in data.values() if not v.strip())
    print(f"Saved {path} with {len(data)} texts, {todo} still to translate.")
    print("Fill in each value in that language: natural words, same {placeholders} and HTML tags as the English key.")
    print(f"Then check it: python -m encryptor_mcp.i18n --check {code}. The pages use it after a restart.")


if __name__ == "__main__":
    translate(sys.argv[1:])
