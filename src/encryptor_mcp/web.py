# SPDX-License-Identifier: AGPL-3.0-only
"""The local unlock page: a tiny web server on 127.0.0.1 only, started with the MCP server.

GET  /unlock/<code>            the form (the code works once, for 5 minutes)
POST /unlock/<code>            password, how long, read only
GET  /vault/<status code>      what's open and for how long
POST /vault/<status code>/lock lock now
GET  /vault/<status code>/files/<folder>/   browse a folder
GET  /vault/<status code>/open/<file>       view a text file, picture or PDF in the browser (sandboxed)
GET  /vault/<status code>/get/<file>        download a file (decrypted)
POST /vault/<status code>/mount, /unmount   show the vault in Finder (or the file manager), or remove it
The status code is a long random secret shown only to the person, in their browser, after unlocking.
Requests must name this server's own address (no other host names: protection against DNS rebinding), and form
posts must come from this server's own pages.
"""

from __future__ import annotations

import mimetypes
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import changes, pages
from .vault import keys
from .unlock import UnlockManager, UnlockRefused

MAX_FORM = 8 * 1024
VIEWABLE = {"image/png", "image/jpeg", "image/gif", "image/webp"}   # PDFs: download only (no viewer in the sandbox)
FILE_HEADERS = {   # decrypted files can't run anything, load anything, or reach these pages
    "Content-Security-Policy": "sandbox; default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; "
                               "frame-ancestors 'none'",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def _kind(name: str, data: bytes) -> str | None:
    """The type to show a file as in the browser, or None to only offer the download."""
    guess = mimetypes.guess_type(name)[0] or ""
    if guess in VIEWABLE:
        return guess
    if guess.startswith("text/") or guess in ("application/json", "application/xml", "") or name.endswith((".md", ".csv")):
        if b"\x00" not in data[:8192]:
            try:
                data.decode("utf-8")
                return "text/plain; charset=utf-8"
            except UnicodeDecodeError:
                return None
    return None


def _status(manager: UnlockManager, s, mounts, note: str = "") -> tuple[int, dict, str]:
    ends = time.strftime("%H:%M", time.localtime(s.expires))
    finder = mounts.label() if mounts and mounts.available() else None
    return 200, {}, pages.unlocked(s.vault.name, s.status_code, s.read_only, s.keep, s.app, ends,
                                   int(manager.idle // 60), finder, mounts.where(s.vault.name) if mounts else "", note)


def _vault_pages(manager: UnlockManager, method: str, parts: list[str], mounts) -> tuple[int, dict, str | bytes]:
    s = manager.by_status_code(parts[1])
    if s is None:
        return 404, {}, pages.message("Locked", "This vault is locked.", ok=True)
    action = parts[2] if len(parts) > 2 else ""
    rel = "/".join(unquote(p) for p in parts[3:])
    if method == "POST" and action == "lock" and len(parts) == 3:
        if mounts:
            mounts.unmount(s.vault.name)
        manager.lock(s.vault.name, "locked on the unlock page")
        return 200, {}, pages.message("Locked", f"{s.vault.name} is locked. The keys are gone from memory.", ok=True)
    if method == "POST" and action in ("mount", "unmount") and len(parts) == 3 and mounts:
        manager.use(s.vault.name)
        try:
            if action == "mount":
                where = mounts.mount(s)
                note = f"Open in {mounts.label()} at {where}."
            else:
                mounts.unmount(s.vault.name)
                note = f"Removed from {mounts.label()}."
        except Exception as exc:   # a plain-words reason from mount.py
            note = str(exc)
        return _status(manager, s, mounts, note)
    if method == "GET" and not action and len(parts) == 2:
        return _status(manager, s, mounts)
    if method != "GET" or action not in ("files", "open", "get"):
        return 404, {}, pages.message("Not found", "There's nothing here.")
    manager.use(s.vault.name)   # looking counts as using the vault
    try:
        e = s.tree.resolve(changes.clean(rel))
    except keys.VaultError as exc:
        return 404, {}, pages.message("Not found", str(exc))
    if action == "files":
        if e.kind != "dir":
            return 404, {}, pages.message("Not a folder", f"'{rel}' isn't a folder.")
        rows = []
        for item in s.tree.list_dir(e.dir_id):
            if e.dir_id == b"" and item.name.casefold() == changes.META:
                continue
            date = time.strftime("%Y-%m-%d %H:%M", time.localtime(item.stored.stat().st_mtime))
            if item.kind == "file":
                size = _size(s.tree.file_size(item))
                viewable = (mimetypes.guess_type(item.name)[0] or "") in VIEWABLE or _maybe_text(item.name)
                rows.append((item.name, "file", size, date, viewable))
            else:
                rows.append((item.name, item.kind, "", date, False))
        return 200, {}, pages.browse(s.vault.name, s.status_code, rel, rows)
    if e.kind != "file":
        return 404, {}, pages.message("Not a file", f"'{rel}' isn't a file.")
    data = s.tree.read_file(e)
    manager._event(s.vault.name, f"{'viewed' if action == 'open' else 'downloaded'} {rel} on the browse page")
    name = e.name
    if action == "open":
        kind = _kind(name, data)
        if kind is None:
            return 200, {}, pages.message("Can't show this here", f"'{name}' can't be shown in the browser. Download it instead.")
        return 200, {**FILE_HEADERS, "Content-Type": kind}, data
    ascii_name = name.encode("ascii", "replace").decode().replace('"', "_").replace("?", "_")
    return 200, {**FILE_HEADERS, "Content-Type": "application/octet-stream",
                 "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"}, data


def _maybe_text(name: str) -> bool:
    guess = mimetypes.guess_type(name)[0] or ""
    return guess.startswith("text/") or guess in ("application/json", "application/xml") or name.endswith((".md", ".csv"))


def _size(n: float) -> str:
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{int(n)} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)


def handle(manager: UnlockManager, method: str, path: str, form: dict, headers: dict, base: str,
           mounts=None) -> tuple[int, dict, str | bytes]:
    """Framework-free: (status, extra headers, html). Also used by the web version later."""
    parts = [p for p in path.split("?")[0].split("/") if p]
    if method == "POST" and not same_origin(headers, base):
        return 403, {}, pages.message("Not allowed", "This form didn't come from this page.")
    if len(parts) == 2 and parts[0] == "unlock":
        code = parts[1]
        req = manager.describe(code)
        if req is None:
            return 410, {}, pages.message("Link expired", "This unlock link has expired or was already used. "
                                          "Ask your AI app to unlock the vault again.")
        if method == "GET":
            return 200, {}, pages.unlock_form(code, req.vault, req.app, req.purpose,
                                              idle_minutes=int(manager.idle // 60))
        try:
            s = manager.unlock(code, form.get("password", ""), form.get("keep", "lock"), form.get("read_only") == "yes")
        except UnlockRefused as exc:
            time.sleep(1)   # slows down guessing
            return 401, {}, pages.unlock_form(code, req.vault, req.app, req.purpose, str(exc),
                                              idle_minutes=int(manager.idle // 60))
        return 303, {"Location": f"/vault/{s.status_code}"}, ""
    if len(parts) >= 2 and parts[0] == "vault":
        return _vault_pages(manager, method, parts, mounts)
    return 404, {}, pages.message("Not found", "There's nothing here.")


def same_origin(headers: dict, base: str) -> bool:
    origin = headers.get("origin")
    if origin and origin != "null":
        return origin.rstrip("/") == base
    return headers.get("sec-fetch-site", "same-origin") in ("same-origin", "none")


class LocalPages:
    """The unlock page on 127.0.0.1, on a free port, in a background thread."""

    def __init__(self, manager: UnlockManager, port: int = 0, mounts=None):
        self.manager = manager
        self.mounts = mounts
        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "Encryptor"
            sys_version = ""

            def log_message(self, *args):   # nothing about requests goes to the console
                pass

            def _serve(self, method: str):
                headers = {k.lower(): v for k, v in self.headers.items()}
                if headers.get("host") not in outer.allowed_hosts:
                    return self._send(421, {}, "Wrong address.")
                form = {}
                if method == "POST":
                    length = int(headers.get("content-length") or 0)
                    if length > MAX_FORM:
                        return self._send(413, {}, "Too large.")
                    raw = self.rfile.read(length).decode("utf-8", "replace")
                    form = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
                status, extra, body = handle(outer.manager, method, urlparse(self.path).path, form, headers, outer.base,
                                             outer.mounts)
                self._send(status, extra, body)

            def _send(self, status: int, extra: dict, body: str | bytes):
                data = body if isinstance(body, bytes) else body.encode()
                self.send_response(status)
                for k, v in {**pages.HEADERS, "Content-Type": "text/html; charset=utf-8", **extra}.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._serve("GET")

            def do_POST(self):
                self._serve("POST")

        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.port = self.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.allowed_hosts = {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}
        threading.Thread(target=self.httpd.serve_forever, name="unlock-page", daemon=True).start()

    def unlock_url(self, code: str) -> str:
        return f"{self.base}/unlock/{code}"

    def close(self) -> None:
        self.httpd.shutdown()
