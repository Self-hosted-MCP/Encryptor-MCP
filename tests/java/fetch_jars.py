# SPDX-License-Identifier: AGPL-3.0-only
"""Downloads Cryptomator's own libraries (the versions Cryptomator 1.19.3 ships) from Maven Central, for the
reference checks on machines without Cryptomator.app (Windows, Linux, CI). Every file is checked against a pinned
SHA-256; nothing else is fetched or run.

    python tests/java/fetch_jars.py <folder>      then: CRYPTOMATOR_MODS=<folder> pytest
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

CENTRAL = "https://repo1.maven.org/maven2"
JARS = {  # group:artifact:version -> sha256
    "org.cryptomator:cryptofs:2.10.0": "bca4f7bf7dd8e16f4c21ea96f15d4d2205ce35240c5f6ff09d28418470d4c82f",
    "org.cryptomator:cryptolib:2.2.2": "8deac22a954c2058d5ad325168b73c1b4d245eeba178e70b2b78a3947f37188f",
    "org.cryptomator:siv-mode:1.6.1": "7d2b927818d981bd5549fb522d0df7b47522b1fde9c1a7b120965ea41e4f84d2",
    "com.auth0:java-jwt:4.5.2": "d59552b5e39e3f5e021df37f3e9471586c3d578b98d81e40fb1fe3aecd599661",
    "com.fasterxml.jackson.core:jackson-databind:2.21.4": "3888e9e69ab66fbacaacc9aea0e9ffbf15368288e4aca468b024dba11c09fbf9",
    "com.fasterxml.jackson.core:jackson-core:2.21.4": "4b40a06396f239f8de2da57419adde6e94e5edc18a2171d471ea05eeed4e5c2d",
    "com.fasterxml.jackson.core:jackson-annotations:2.21": "53ca085f4a150f703f49e1aabd935bd03b43e1ea3d55d135438292af22cef56b",
    "com.github.ben-manes.caffeine:caffeine:3.2.4": "9d9d2cfd681fd9272ded3d27c9930db12f89f732345975aa113ebc223bbf1224",
    "com.google.dagger:dagger:2.59.2": "f449e1b07cc65dce15e3df8316d0d3a27ee601601abf957074fe810f545feab5",
    "jakarta.inject:jakarta.inject-api:2.0.1": "f7dc98062fccf14126abb751b64fab12c312566e8cbdc8483598bffcea93af7c",
    "javax.inject:javax.inject:1": "91c77044a50c481636c32d916fd89c9118a72195390452c81065080f957de7ff",
    "org.slf4j:slf4j-api:2.0.18": "44508fd1576500688c790b190acdd16fec4f8c79a3e0b900afd70503cf055f55",
    "com.google.code.gson:gson:2.13.2": "dd0ce1b55a3ed2080cb70f9c655850cda86c206862310009dcb5e5c95265a5e0",
    "org.jspecify:jspecify:1.0.0": "1fad6e6be7557781e4d33729d49ae1cdc8fdda6fe477bb0cc68ce351eafdfbab",
    "com.google.errorprone:error_prone_annotations:2.49.0": "3b1003e51b8ae56fdbd7c71073e81d1683b97e6c4dff5a9151164d59b769d13c",
    "com.google.guava:guava:33.5.0-jre": "1e301f0c52ac248b0b14fdc3d12283c77252d4d6f48521d572e7d8c4c2cc4ac7",
    "com.google.guava:failureaccess:1.0.3": "cbfc3906b19b8f55dd7cfd6dfe0aa4532e834250d7f080bd8d211a3e246b59cb",
}


def main(folder: str) -> None:
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    for coord, pinned in JARS.items():
        group, artifact, ver = coord.split(":")
        name = f"{artifact}-{ver}.jar"
        target = out / name
        if not target.exists():
            url = f"{CENTRAL}/{group.replace('.', '/')}/{artifact}/{ver}/{name}"
            with urllib.request.urlopen(url, timeout=60) as r:
                target.write_bytes(r.read())
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if pinned and digest != pinned:
            target.unlink()
            sys.exit(f"Checksum mismatch for {name}: refusing to use it.")
        print(f"{digest}  {name}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "jars")
