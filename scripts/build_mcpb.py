# SPDX-License-Identifier: AGPL-3.0-only
"""Builds the Claude Desktop extension: dist/encryptor-mcp-<version>.mcpb.

    python3 scripts/build_mcpb.py

An .mcpb file is a zip: extension/manifest.json (with this version filled in) plus the project itself. Claude
Desktop runs it with uv, which brings Python and the exact packages in uv.lock, so nothing needs installing
first. Only the package and the files uv needs go in: never tests, .tools, .jars, .venv, .impeccable or vaults.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["pyproject.toml", "uv.lock", "README.md", "LICENSE", "NOTICE"]   # what uv needs to install it
OPTIONAL = ["CHANGELOG.md"]
SKIP = {"__pycache__", ".DS_Store", "tests", ".tools", ".jars", ".venv", ".impeccable", "vaults"}


def version() -> str:
    found = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M)
    if not found:
        sys.exit("No version in pyproject.toml.")
    return found.group(1)


def build(out_dir: Path = ROOT / "dist") -> Path:
    ver = version()
    manifest = json.loads((ROOT / "extension" / "manifest.json").read_text())
    manifest["version"] = ver
    icon = ROOT / "extension" / "icon.png"   # 512 px, the size Claude Desktop shows best
    if icon.exists():
        manifest["icon"] = "icon.png"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"encryptor-mcp-{ver}.mcpb"
    package = ROOT / "src" / "encryptor_mcp"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
        if icon.exists():
            zf.write(icon, "icon.png")
        for name in FILES + [n for n in OPTIONAL if (ROOT / n).exists()]:
            zf.write(ROOT / name, name)
        for path in sorted(package.rglob("*")):
            rel = path.relative_to(ROOT)
            if path.is_file() and not SKIP & set(rel.parts) and path.suffix != ".pyc":
                zf.write(path, rel.as_posix())
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print((__doc__ or "").strip())
    else:
        print(build())
