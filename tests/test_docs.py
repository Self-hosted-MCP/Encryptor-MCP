# SPDX-License-Identifier: AGPL-3.0-only
"""The docs stay true: every link and anchor works, every setting and tool is documented, no em dashes."""
import asyncio
import re
from pathlib import Path

from encryptor_mcp import server

ROOT = Path(__file__).resolve().parent.parent
DOCS = sorted([*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md")])
LINK = re.compile(r"\]\(([^)\s]+)\)|href=\"([^\"]+)\"|src=\"([^\"]+)\"")


def slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    text = re.sub(r"[`*_]|<[^>]+>", "", heading.strip().lower())
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    out = set()
    in_code = False
    for line in path.read_text("utf-8").splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if in_code or not line.startswith("#"):
            continue
        s = slug(line.lstrip("#"))
        n = seen.get(s, 0)
        seen[s] = n + 1
        out.add(s if n == 0 else f"{s}-{n}")
    return out


def test_links_and_anchors_work():
    broken = []
    for doc in DOCS:
        text = re.sub(r"```.*?```", "", doc.read_text("utf-8"), flags=re.S)
        for m in LINK.finditer(text):
            target = next(g for g in m.groups() if g)
            if re.match(r"[a-z]+:", target) or target.startswith("//"):
                continue
            path, _, anchor = target.partition("#")
            dest = (doc.parent / path).resolve() if path else doc
            if not dest.exists():
                broken.append(f"{doc.name}: {target}")
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                broken.append(f"{doc.name}: {target} (no such heading)")
    assert not broken, "\n".join(broken)


def test_every_setting_is_documented():
    settings = (ROOT / "docs" / "settings.md").read_text("utf-8")
    example = (ROOT / ".env.example").read_text("utf-8")
    names = set(server.SETTINGS) | {"ENCRYPTOR_CONFIG_DIR", "ENCRYPTOR_DATA_DIR", "ENCRYPTOR_ENV_FILE"}
    missing = sorted(n for n in names if n not in settings)
    assert not missing, f"not in docs/settings.md: {missing}"
    set_by_hosts = {"RENDER_EXTERNAL_URL", "RAILWAY_PUBLIC_DOMAIN"}   # those hosts set them; nobody types them
    missing = sorted(n for n in server.SETTINGS if n not in example and n not in set_by_hosts)
    assert not missing, f"not in .env.example: {missing}"


def test_every_tool_is_documented():
    tools = (ROOT / "docs" / "tools.md").read_text("utf-8")
    names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    assert len(names) == 23
    assert not [n for n in names if f"`{n}`" not in tools]


def test_no_em_dashes():
    found = [f"{d.name}:{i}" for d in DOCS for i, line in enumerate(d.read_text("utf-8").splitlines(), 1)
             if "—" in line or " – " in line]
    assert not found, found
