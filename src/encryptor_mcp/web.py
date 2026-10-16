# SPDX-License-Identifier: AGPL-3.0-only
"""The local unlock page: a tiny web server on 127.0.0.1 only, started with the MCP server.

GET  /unlock/<code>            the form (the code works once, for 5 minutes)
POST /unlock/<code>            password, how long, read only
GET  /vault/<status code>      what's open and for how long
POST /vault/<status code>/lock lock now
Requests must name this server's own address (no other host names: protection against DNS rebinding), and form
posts must come from this server's own pages.
"""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import pages
from .unlock import UnlockManager, UnlockRefused

MAX_FORM = 8 * 1024


def handle(manager: UnlockManager, method: str, path: str, form: dict, headers: dict, base: str) -> tuple[int, dict, str]:
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
        s = manager.by_status_code(parts[1])
        if s is None:
            return 404, {}, pages.message("Locked", "This vault is locked.", ok=True)
        if method == "POST" and len(parts) == 3 and parts[2] == "lock":
            manager.lock(s.vault.name, "locked on the unlock page")
            return 200, {}, pages.message("Locked", f"{s.vault.name} is locked. The keys are gone from memory.", ok=True)
        if method == "GET" and len(parts) == 2:
            ends = time.strftime("%H:%M", time.localtime(s.expires))
            return 200, {}, pages.unlocked(s.vault.name, s.status_code, s.read_only, s.keep, s.app, ends,
                                           int(manager.idle // 60))
    return 404, {}, pages.message("Not found", "There's nothing here.")


def same_origin(headers: dict, base: str) -> bool:
    origin = headers.get("origin")
    if origin and origin != "null":
        return origin.rstrip("/") == base
    return headers.get("sec-fetch-site", "same-origin") in ("same-origin", "none")


class LocalPages:
    """The unlock page on 127.0.0.1, on a free port, in a background thread."""

    def __init__(self, manager: UnlockManager, port: int = 0):
        self.manager = manager
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
                status, extra, body = handle(outer.manager, method, urlparse(self.path).path, form, headers, outer.base)
                self._send(status, extra, body)

            def _send(self, status: int, extra: dict, body: str):
                data = body.encode()
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
