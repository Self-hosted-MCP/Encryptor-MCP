# SPDX-License-Identifier: AGPL-3.0-only
"""Languages for the pages: picking one, falling back to English, every shipped file complete and safe, the
command that makes a new one, and no English text left out of the translations."""
import html as htmllib
import json
import re

import pytest

from encryptor_mcp import i18n, pages, server
from test_center import PW, local, setup  # noqa: F401  (fixtures)


@pytest.fixture
def locales(tmp_path, monkeypatch):
    """A private locales folder holding a small test language, 'xx', and no shipped ones."""
    monkeypatch.setattr(i18n, "user_locales", lambda: tmp_path)
    monkeypatch.setattr(i18n, "PACKAGE_LOCALES", tmp_path / "none")
    i18n._catalogs.clear()
    (tmp_path / "xx.json").write_text(json.dumps({
        "Vault password": "Kluiswachtwoord-xx",
        "Your vaults": "Je kluizen-xx",
        "Unlock {vault}": "Ontgrendel {vault}-xx",
        "Wrong passphrase.": "Verkeerd-xx.",
        "Or just ask your AI app: <b>“Open my Encryptor control center.”</b> It opens right here, already signed in.":
            "Vraag je AI-app: <b>“Open mijn bedieningscentrum.”</b> xx",
        "Sign in": "",
    }), encoding="utf-8")
    yield tmp_path
    i18n._catalogs.clear()
    i18n.LANG.set("en")


@pytest.fixture
def english():
    yield
    i18n._catalogs.clear()
    i18n.LANG.set("en")


def test_pick_follows_the_browser_and_the_setting(locales):
    assert i18n.pick("xx;q=0.9, en;q=0.5") == "xx"
    assert i18n.pick("en;q=0.9, xx;q=0.5") == "en"
    assert i18n.pick("de-DE, de;q=0.9") == "en"                  # no German file here: English
    assert i18n.pick("xx-YY") == "xx"                             # a regional variant finds the base language
    assert i18n.pick("xx", forced="en") == "en"                   # ENCRYPTOR_LANGUAGE wins over the browser
    assert i18n.pick("en", forced="xx") == "xx"
    assert i18n.pick("xx;q=0") == "en"                            # q=0 means "not this one"
    assert i18n.pick("") == "en" and i18n.pick("!!, ;q=x") == "en"


def test_shipped_language_codes_match_variants(english):
    i18n._catalogs.clear()
    assert i18n.pick("zh-HK") == "zh-TW" and i18n.pick("zh-Hant") == "zh-TW"
    assert i18n.pick("zh-Hans-CN") == "zh-CN" and i18n.pick("zh") == "zh-CN"
    assert i18n.pick("pt-PT") == "pt-BR" and i18n.pick("de-AT") == "de" and i18n.pick("ja-JP") == "ja"


def test_missing_texts_fall_back_to_english(locales):
    i18n.LANG.set("xx")
    assert i18n._("Vault password") == "Kluiswachtwoord-xx"
    assert i18n._("Sign in") == "Sign in"                         # empty: English
    assert i18n._("Lock all") == "Lock all"                       # not in the file: English
    assert i18n._("Unlock {vault}", vault="Taxes") == "Ontgrendel Taxes-xx"


def test_every_shipped_language_is_complete_and_safe():
    """Each shipped file has every page text, with the same placeholders and tags, and nothing extra or stale."""
    texts = i18n.source_texts()
    assert len(texts) > 250
    shipped = sorted(p.stem for p in i18n.PACKAGE_LOCALES.glob("*.json"))
    assert shipped == sorted(c for c in i18n.LANGUAGES if c != "en")
    for code in shipped:
        data = json.loads((i18n.PACKAGE_LOCALES / f"{code}.json").read_text(encoding="utf-8"))
        missing = [t for t in texts if not str(data.get(t, "")).strip()]
        assert not missing, f"{code}: missing {missing[:5]}"
        assert not [k for k in data if k not in texts], f"{code}: texts no page uses any more"
        broken = [(t, p) for t in texts for p in i18n.problems(t, data[t])]
        assert not broken, f"{code}: {broken[:5]}"
        assert not [t for t in data.values() if "—" in t], f"{code}: em dash"


def test_pages_speak_the_browsers_language(local, monkeypatch, english):
    client, lp, _setup = local
    page = client.get("/", headers={"accept-language": "de-DE,de;q=0.9,en;q=0.5"}).text
    assert 'lang="de"' in page and "Tresor" in page
    page = client.get("/", headers={"accept-language": "ja"}).text
    assert 'lang="ja"' in page
    assert 'lang="en"' in client.get("/").text
    assert 'lang="en"' in client.get("/", headers={"accept-language": "xx-unknown"}).text
    monkeypatch.setenv("ENCRYPTOR_LANGUAGE", "fr")          # the setting wins over the browser
    page = client.get("/", headers={"accept-language": "de"}).text
    assert 'lang="fr"' in page
    monkeypatch.setenv("ENCRYPTOR_LANGUAGE", "nonsense")    # unknown: back to the browser
    assert 'lang="de"' in client.get("/", headers={"accept-language": "de"}).text


def test_a_whole_flow_in_german(local, english):
    """Unlock in German: the form, a wrong password's page, then the vault's own page."""
    client, lp, (v1, _v2) = local
    de = {"accept-language": "de", "origin": lp.base}
    code = lp.manager.request_unlock("GCM", "Claude", "taxes")
    page = client.get(f"/unlock/{code}", headers=de).text
    i18n.LANG.set("de")
    assert i18n._("Vault password") in page and i18n._("Keep it open") in page and "Vault password" not in page
    r = client.post(f"/unlock/{code}", data={"password": PW, "keep": "lock"}, headers=de, follow_redirects=False)
    page = client.get(r.headers["location"], headers=de).text
    assert i18n._("Lock now") in page and "GCM" in page and "Lock now" not in page


def test_values_in_translations_are_escaped(locales):
    i18n.LANG.set("xx")
    html = pages.unlock_form("c0de", "<script>x</script>", "Claude", "")
    assert "<script>x</script>" not in html and "Ontgrendel &lt;script&gt;x&lt;/script&gt;-xx" in html
    assert "Kluiswachtwoord-xx" in html and 'lang="xx"' in html
    assert "<b>“Open mijn bedieningscentrum.”</b>" in pages.signin(False)


def test_problems_catch_broken_translations():
    assert i18n.problems("Unlock {vault}", "Entsperren {tresor}")
    assert i18n.problems("Or just ask: <b>x</b>", "Frag einfach: x")
    assert i18n.problems("Save", "<script>alert(1)</script>")
    assert i18n.problems("Lent to {app}", "Verliehen an {app")
    assert not i18n.problems("Lent to {app}", "Verliehen an {app}")


def test_a_broken_translation_never_breaks_a_page(locales):
    (locales / "xx.json").write_text(json.dumps({"Lent to {app}": "Verliehen an {ap",
                                                 "Save": "<script>alert(1)</script>"}), encoding="utf-8")
    i18n._catalogs.clear()
    i18n.LANG.set("xx")
    assert i18n._("Lent to {app}", app="Claude") == "Lent to Claude"
    assert i18n._("Save") == "Save"                               # unsafe translations aren't even loaded


def test_the_translate_command(locales, capsys):
    i18n.translate(["ko"])
    data = json.loads((locales / "ko.json").read_text(encoding="utf-8"))
    assert "Vault password" in data and "Unlock {vault}" in data and len(data) > 250
    assert all(v == "" for v in data.values())
    data["Vault password"] = "볼트 비밀번호"
    data["Unlock {vault}"] = "{vault} 잠금 해제"
    (locales / "ko.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    i18n.translate(["ko"])                                        # running again keeps what's filled in
    again = json.loads((locales / "ko.json").read_text(encoding="utf-8"))
    assert again["Vault password"] == "볼트 비밀번호"
    with pytest.raises(SystemExit, match="still to translate"):
        i18n.translate(["--check", "ko"])
    assert "2 of" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="Usage"):
        i18n.translate(["../evil"])


def sample_pages() -> str:
    """Every page, fully drawn with made-up data, in the current language."""
    class Finding:
        def __init__(self, severity, fix):
            self.severity, self.fix, self.where, self.detail, self.kind = severity, fix, "/Notes", "x", "Missing"
    vault = {"name": "Taxes", "status_code": "s", "read_only": False, "keep": "lock", "app": "Claude",
             "ends_at": "18:30", "idle_minutes": 10, "finder": "Finder", "mounted": "/Volumes/Taxes", "note": "",
             "center": True, "center_link": "/",
             "changes": [{"id": "1", "when": "01 Oct 10:00", "action": "write", "path": "a.md", "to": "", "app": "Claude",
                          "purpose": "", "undone": True, "undoable": True}],
             "trash": [{"change": "2", "path": "b.md", "kind": "file", "when": "01 Oct 10:00", "app": "Claude"},
                       {"change": "3", "path": "c", "kind": "dir", "when": "01 Oct 10:00", "app": "Claude"}],
             "health": (1, [Finding("critical", "x"), Finding("warn", ""), Finding("info", "")]),
             "reads": {"entries": [{"time": 1, "how": "read", "path": "a.md", "who": "Claude", "purpose": ""}],
                       "verdict": "Intact: 1 entries, each checked against the one before."}}
    rows = [{"name": "Taxes", "mode": "full", "open": True, "read_only": True, "status_code": "s", "app": "Claude",
             "ends_at": "18:30"},
            {"name": "Notes", "mode": "read", "open": False, "read_only": True, "status_code": "", "app": "",
             "ends_at": ""},
            {"name": "Diary", "mode": "hidden", "open": False, "read_only": False, "status_code": "", "app": "",
             "ends_at": ""}]
    home = {"vaults": rows, "default": "Taxes", "csrf": "t", "note": "", "hosted": True, "read_only_all": True,
            "apps": [{"id": "a", "name": "Claude", "vaults": [], "change": True},
                     {"id": "b", "name": "ChatGPT", "vaults": ["Taxes"], "change": False}]}
    setting_rows = [{"name": "Taxes", "mode": "full", "idle": 5, "default": True}, {"name": "Notes", "mode": "read"}]
    settings = {"vaults": setting_rows, "csrf": "t", "note": "", "error": "", "hosted": False, "idle_minutes": 10,
                "idle_fixed": False, "read_only_all": False, "read_only_fixed": True, "allow_purge": True,
                "mcp_url": "https://vault.example.com/mcp"}
    activity = {"csrf": "t", "devices": [{"id": "d", "agent": "", "this": True, "since": 1, "seen": 1,
                                          "ip": "1.2.3.4", "remember": True},
                                         {"id": "e", "agent": "Safari on Mac", "this": False, "since": 1, "seen": 1}],
                "log": [{"time": 1, "ok": True, "how": "passphrase", "agent": "Safari on Mac", "ip": ""},
                        {"time": 1, "ok": False, "how": "expired link", "agent": "Safari on Mac", "ip": ""}]}
    about = {"csrf": "t", "version": "0.1.0", "repo": "a/b", "update_check": True,
             "update": {"newer": True, "latest": "0.2.0"}}
    vset = {"vault": {"name": "Taxes", "path": "/v/Taxes", "mode": "full", "mode_fixed": False, "idle": 5},
            "csrf": "t", "note": "", "error": "", "open": True, "app": "Claude", "status_code": "s",
            "format": "x", "idle_all": 10}
    return "".join([
        pages.unlock_form("c", "Taxes", "Claude", "for the taxes"),
        pages.unlock_form("c", "Taxes", "Claude", "", center=True, by_person=True),
        pages.vault_page(vault), pages.vault_page({**vault, "mounted": "", "health": (1, []), "trash": [],
                                                    "changes": [], "reads": {"entries": [], "verdict": "Nothing read yet."}}),
        pages.vault_page({**vault, "health": None}),
        pages.browse("Taxes", "s", "2026/May", [("Receipts", "dir", "", "2026-10-01", False),
                                               ("a.pdf", "file", "1 MB", "2026-10-01", False),
                                               ("l", "link", "", "", False)]),
        pages.browse("Taxes", "s", "", []),
        pages.center_home(home), pages.center_home({**home, "vaults": [], "apps": []}),
        pages.settings(settings), pages.settings({**settings, "vaults": [], "idle_fixed": True}),
        pages.activity(activity), pages.activity({"csrf": "t"}),
        pages.about(about), pages.about({**about, "update": {"latest": "0.1.0"}}),
        pages.vault_settings(vset),
        pages.vault_settings({**vset, "open": False, "vault": {**vset["vault"], "mode_fixed": True}}),
        pages.confirm_change({"csrf": "t", "action": "/x", "title": "x", "button": "x", "fields": {}, "lines": []}),
        pages.app_access({"id": "a", "app": "Claude", "csrf": "t", "vaults": ["Taxes"], "granted": [], "change": True}),
        pages.app_access({"id": "a", "app": "Claude", "csrf": "t", "vaults": [], "granted": [], "change": True}),
        pages.recovery_page({"vault": "Taxes", "key": "word " * 44, "back": "/", "csrf": "t"}),
        pages.signin(True), pages.signin(False, "", ["Taxes"]), pages.signin(False),
        pages.app_login(("Claude", "claude.ai"), "r", ["Taxes"]), pages.app_login(("Claude", "claude.ai"), "r", []),
        pages.app_login(None, "r", []), pages.message("x", "x", center=True),
    ])


def test_every_page_text_is_marked_for_translation(english):
    """Catches a new English sentence added to a page without _(): every text between tags on a fully drawn page
    must be one of the translatable texts (or a name, a number or made-up data)."""
    texts = i18n.source_texts()
    plain = [re.sub(r"<[^>]+>", "", t) for t in texts]
    pieces = [f.strip(" .") for t in texts for f in re.split(r"<[^>]+>", t) if f.strip(" .")]
    patterns = [re.compile("^" + re.sub(r"\\\{\w+\\\}", ".+", re.escape(f)) + "$") for f in pieces]
    allowed = {"Taxes", "Notes", "Diary", "Claude", "ChatGPT", "Safari on Mac", "Receipts", "for the taxes", "word",
               "Encryptor MCP", "AGPL-3.0", "Finder", "Missing", "May", "a.pdf", "2026", "word", "https://vault.example.com/mcp", "claude.ai"}
    html = re.sub(r"<style>.*?</style>|<!--.*?-->", "", sample_pages(), flags=re.S)
    data = sorted(allowed | {"a.md", "b.md", "/v/Taxes", "/Notes", "18:30", "01 Oct 10:00", "1.2.3.4"}, key=len,
                  reverse=True)
    checked = 0
    for chunk in re.findall(r">([^<>]*[A-Za-z]{2,}[^<>]*)<", html):
        chunk = re.sub(r" · Encryptor MCP$", "", htmllib.unescape(chunk))
        if chunk.strip() in allowed:
            continue
        for word in data:   # made-up data inside a sentence: check the words around it
            chunk = chunk.replace(word, "\0")
        for piece in chunk.split("\0"):
            piece = piece.strip(" .·,→:")
            if not re.search(r"[A-Za-z]{2,}", piece) or re.fullmatch(r"[\w./-]*\d[\w./ :-]*|x", piece):
                continue
            checked += 1
            assert any(piece in t for t in plain) or any(p.search(piece) for p in patterns), piece
    assert checked > 150


def test_every_page_draws_in_every_language(english):
    """No shipped translation breaks a page: each one draws every page, in its own language."""
    for code in i18n.LANGUAGES:
        i18n.LANG.set(code)
        html = sample_pages()
        assert f'lang="{code}"' in html and "{" not in re.sub(r"<style>.*?</style>", "", html, flags=re.S)


def test_the_setting_is_known():
    assert "ENCRYPTOR_LANGUAGE" in server.SETTINGS
