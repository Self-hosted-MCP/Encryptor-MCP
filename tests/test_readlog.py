# SPDX-License-Identifier: AGPL-3.0-only
"""The read log: private, encrypted, and any edit, removal or reordering shows."""
from conftest import FIXTURES, password
from encryptor_mcp.readlog import ReadLog
from encryptor_mcp.vault import keys


def make(tmp_path, clock=None):
    key = keys.unlock_masterkey((FIXTURES / "vault-SIV_GCM" / "masterkey.cryptomator").read_bytes(), password("SIV_GCM"))
    return ReadLog(tmp_path, key, "vault-1", **({"clock": clock} if clock else {}))


def fill(log):
    log.add("Claude", "/Taxes/2025.pdf", "read", "sum up the year")
    log.add("You", "/Taxes/receipt.png", "viewed")
    log.add("Cursor", "/notes.md", "read", "draft")


def test_entries_and_privacy(tmp_path):
    log = make(tmp_path)
    fill(log)
    entries, verdict = log.read()
    assert [e["path"] for e in entries] == ["/notes.md", "/Taxes/receipt.png", "/Taxes/2025.pdf"]
    assert entries[-1]["purpose"] == "sum up the year" and verdict.startswith("Intact: 3 entries")
    raw = log.path.read_text() + log.head_path.read_text()
    assert "Taxes" not in raw and "Claude" not in raw                       # encrypted
    assert oct(log.path.stat().st_mode)[-3:] == "600"


def test_changed_line_is_caught(tmp_path):
    log = make(tmp_path)
    fill(log)
    lines = log.path.read_text().splitlines()
    lines[1] = lines[1][:-2] + ("00" if lines[1][-2:] != "00" else "11")
    log.path.write_text("\n".join(lines) + "\n")
    entries, verdict = log.read()
    assert "Entry 2 was changed" in verdict and len(entries) == 1


def test_removed_or_reordered_lines_are_caught(tmp_path):
    for edit, words in ((lambda l: [l[0], l[2]], "Entry 2"), (lambda l: [l[1], l[0], l[2]], "Entry 1"),
                        (lambda l: l[:2], "The last 1 entries were removed")):
        log = make(tmp_path / words.replace(" ", "_"))
        fill(log)
        lines = log.path.read_text().splitlines()
        log.path.write_text("\n".join(edit(lines)) + "\n")
        assert words in log.read()[1]


def test_finder_looks_count_once(tmp_path):
    now = [1000.0]
    log = make(tmp_path, clock=lambda: now[0])
    for _ in range(5):
        log.add("Finder", "/a.txt", "opened in Finder", once_per=600)
    now[0] += 601
    log.add("Finder", "/a.txt", "opened in Finder", once_per=600)
    assert len(log.read()[0]) == 2


def test_wrong_vault_key_reads_nothing(tmp_path):
    log = make(tmp_path)
    fill(log)
    key = keys.unlock_masterkey((FIXTURES / "vault-SIV_CTRMAC" / "masterkey.cryptomator").read_bytes(), password("SIV_CTRMAC"))
    other = ReadLog(tmp_path, key, "vault-1")
    assert other.read()[0] == [] and "Entry 1" in other.read()[1]
