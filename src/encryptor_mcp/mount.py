# SPDX-License-Identifier: AGPL-3.0-only
"""Show an open vault in Finder: a WebDAV server on 127.0.0.1 only, over the vault, mounted by macOS.

- Files are decrypted in memory as Finder reads them and encrypted as it saves; nothing readable is written to
  disk by this program.
- Only this computer can reach it (127.0.0.1, the Host header checked), only at an address with a long random
  secret in it (made for this mount, like Cryptomator's own WebDAV mount), and only from programs of the same Mac
  user: each new connection is checked with lsof, which shows a user only their own programs' connections.
  (A login can't be used: macOS asks for it in a dialog that can't be filled in for the person.)
- Every change goes through the change log like the AI's changes (the app is "Finder"): saving keeps the old
  version, deleting puts things in the vault's trash, and everything can be undone.
- Finder's own files (.DS_Store, ._ files and the like) are kept in memory only and never reach the vault.
  .metadata_never_index asks Spotlight not to index the volume.
- It's removed when the vault locks, when asked on the status page, or when this program stops.
Only reading and writing count as using the vault: Finder's background checks don't keep it open.
"""

from __future__ import annotations

import io
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path

from . import changes
from .vault.keys import VaultError
from .vault.tree import Entry

DEBUG = bool(__import__("os").environ.get("ENCRYPTOR_DAV_DEBUG"))
MAX_PUT = 512 * 1024 * 1024        # files saved from Finder are held in memory (never on disk), so there's a cap
CACHE_SECONDS = 2.0
JUNK_NAMES = {".DS_Store", ".Spotlight-V100", ".Trashes", ".fseventsd", ".TemporaryItems", ".hidden", ".apdisk",
              ".VolumeIcon.icns", ".localized", "Icon\r", ".metadata_never_index", ".com.apple.timemachine.donotpresent",
              ".ql_disablethumbnails", ".ql_disablecache"}
ALWAYS_THERE = {".metadata_never_index", ".ql_disablethumbnails", ".ql_disablecache"}   # at the top: no indexing, no thumbnails cache
USE_METHODS = {"GET", "PUT", "MOVE", "COPY", "DELETE", "MKCOL"}


def is_junk(name: str) -> bool:
    return name.startswith("._") or name in JUNK_NAMES


def _dav():
    from wsgidav import util
    from wsgidav.dav_error import (HTTP_FORBIDDEN, HTTP_PRECONDITION_FAILED, HTTP_REQUEST_ENTITY_TOO_LARGE,
                                   DAVError)
    from wsgidav.dav_provider import DAVCollection, DAVNonCollection, DAVProvider
    return locals()


def build_provider(session, journal, manager, readonly: bool, on_read=None):
    d = _dav()
    util, DAVError = d["util"], d["DAVError"]
    FORBIDDEN, TOO_LARGE = d["HTTP_FORBIDDEN"], d["HTTP_REQUEST_ENTITY_TOO_LARGE"]

    def refuse(exc: Exception):
        raise DAVError(FORBIDDEN, context_info=str(exc))

    class Capped(io.BytesIO):
        def write(self, b):
            if self.tell() + len(b) > MAX_PUT:
                raise DAVError(TOO_LARGE, context_info="Files over 512 MB can't be saved through Finder.")
            return super().write(b)

        def close(self):   # wsgidav closes the stream before end_write; keep the data until then
            pass

    class Provider(d["DAVProvider"]):
        def __init__(self):
            super().__init__()
            self.readonly = readonly
            self.tree = session.tree
            self.cache: dict[bytes, tuple[float, dict[str, Entry]]] = {}
            self.junk: dict[str, bytes] = {}
            self.mutex = threading.RLock()

        def is_readonly(self):
            return self.readonly

        def is_open(self) -> bool:
            return manager.by_status_code(session.status_code) is session

        def touch(self, environ):
            if environ.get("REQUEST_METHOD") in USE_METHODS:
                try:
                    manager.use(session.vault.name)
                except Exception:
                    pass

        def listing(self, dir_id: bytes) -> dict[str, Entry]:
            with self.mutex:
                hit = self.cache.get(dir_id)
                if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
                    return hit[1]
                items = {e.name: e for e in self.tree.list_dir(dir_id)
                         if e.kind in ("file", "dir") and not (dir_id == b"" and e.name.casefold() == changes.META)}
                self.cache[dir_id] = (time.monotonic(), items)
                return items

        def changed(self):
            with self.mutex:
                self.cache.clear()

        def entry(self, path: str) -> Entry | None:
            parts = [unicodedata.normalize("NFC", p) for p in path.strip("/").split("/") if p]
            e = self.tree.resolve("/")
            for part in parts:
                if e.kind != "dir":
                    return None
                e = self.listing(e.dir_id).get(part)
                if e is None:
                    return None
            return e

        def get_resource_inst(self, path, environ):
            if not self.is_open():
                return None
            self.touch(environ)
            name = path.rstrip("/").rsplit("/", 1)[-1]
            if name and is_junk(name):
                top = path.strip("/") == name
                if path in self.junk or (top and name in ALWAYS_THERE):
                    return JunkFile(path, environ, self)
                return None
            try:
                e = self.entry(path)
            except VaultError:
                return None
            if e is None:
                return None
            return (Folder if e.kind == "dir" else File)(path, environ, e, self)

        # ------------------------------------------------ changes, all through the change log

        def do(self, what, *args):
            if self.readonly:
                raise DAVError(FORBIDDEN, context_info="This vault is open read only.")
            try:
                rec = what(*args, "Finder", "")
            except VaultError as exc:
                refuse(exc)
            finally:
                self.changed()
            manager._event(session.vault.name, f"{rec['action']} {rec['path']} in Finder")
            return rec

        def move(self, src_path: str, dest_path: str, src_kind: str):
            src_name, dest_name = src_path.rsplit("/", 1)[-1], dest_path.rstrip("/").rsplit("/", 1)[-1]
            if is_junk(src_name) or is_junk(dest_name):
                data = self.junk.pop(src_path, b"")
                if is_junk(dest_name):
                    self.junk[dest_path] = data
                return True
            dest = self.entry(dest_path)
            if dest is not None:
                if src_kind == "file" and dest.kind == "file":
                    self.do(journal.move_over, src_path, dest_path)
                    return True
                self.do(journal.trash, dest_path)
            self.do(journal.move, src_path, dest_path)
            return True

        def copy(self, src_path: str, dest_path: str, e: Entry, deep: bool):
            dest_name = dest_path.rstrip("/").rsplit("/", 1)[-1]
            if is_junk(dest_name):
                return True
            dest = self.entry(dest_path)
            if e.kind == "file":
                if dest is not None and dest.kind == "file":
                    data = self.tree.read_file(e)
                    self.do(journal.write, dest_path, data, journal.etag(dest))
                    return True
                if dest is not None:
                    self.do(journal.trash, dest_path)
                self.do(journal.copy, src_path, dest_path)
                return True
            if dest is not None and dest.kind != "dir":
                self.do(journal.trash, dest_path)
                dest = None
            if dest is None:
                self.do(journal.mkdir, dest_path)
            if deep:
                for name, child in self.listing(e.dir_id).items():
                    self.copy(f"{src_path.rstrip('/')}/{name}", f"{dest_path.rstrip('/')}/{name}", child, True)
            return True

    class _Common:
        def _init(self, e, prov):
            self.e, self.prov = e, prov

        def _stat(self):
            target = self.prov.tree.contents_path(self.e) if self.e.kind == "file" else self.e.stored
            try:
                return target.stat()
            except OSError:
                return None

        def get_creation_date(self):
            st = self._stat()
            return st.st_birthtime if st and hasattr(st, "st_birthtime") else (st.st_ctime if st else None)

        def get_last_modified(self):
            st = self._stat()
            return st.st_mtime if st else None

        def handle_delete(self):
            if self.path.strip("/") == "":
                raise DAVError(FORBIDDEN)
            self.prov.do(journal.trash, self.path)
            return True

        def handle_move(self, dest_path):
            return self.prov.move(self.path, dest_path, self.e.kind)

        def handle_copy(self, dest_path, *, depth_infinity):
            return self.prov.copy(self.path, dest_path, self.e, depth_infinity)

        def support_recursive_move(self, dest_path):
            return False

        def copy_move_single(self, dest_path, *, is_move):
            raise DAVError(FORBIDDEN)

        def delete(self):
            self.handle_delete()

    class Folder(_Common, d["DAVCollection"]):
        def __init__(self, path, environ, e, prov):
            d["DAVCollection"].__init__(self, path, environ)
            self._init(e, prov)

        def get_display_info(self):
            return {"type": "Directory"}

        def get_member_names(self):
            names = list(self.prov.listing(self.e.dir_id))
            base = self.path.rstrip("/") + "/"
            names += [p[len(base):] for p in self.prov.junk if p.startswith(base) and "/" not in p[len(base):]]
            return names   # ALWAYS_THERE answers when asked for, without showing in the folder

        def support_recursive_delete(self):
            return True

        def create_empty_resource(self, name):
            path = util.join_uri(self.path, name)
            if is_junk(name):
                self.prov.junk[path] = b""
                return JunkFile(path, self.environ, self.prov)
            self.prov.do(journal.write, path, b"", "")
            return self.prov.get_resource_inst(path, self.environ)

        def create_collection(self, name):
            path = util.join_uri(self.path, name)
            if is_junk(name):
                raise DAVError(FORBIDDEN)
            self.prov.do(journal.mkdir, path)

    class File(_Common, d["DAVNonCollection"]):
        def __init__(self, path, environ, e, prov):
            d["DAVNonCollection"].__init__(self, path, environ)
            self._init(e, prov)
            self.buf = None

        def get_content_length(self):
            return self.prov.tree.file_size(self.e)

        def get_content_type(self):
            return util.guess_mime_type(self.path, self.environ["wsgidav.config"])

        def get_etag(self):
            st = self._stat()
            return f"{st.st_mtime_ns:x}-{st.st_size:x}" if st else None

        def support_etag(self):
            return True

        def support_ranges(self):
            return True

        def get_content(self):
            try:
                data = self.prov.tree.read_file(self.e)
                if on_read:   # the read log: Finder's repeated looks (previews) count once per 10 minutes
                    on_read(session, unicodedata.normalize("NFC", self.path), "opened in Finder")
                return io.BytesIO(data)
            except VaultError as exc:
                refuse(exc)

        def begin_write(self, *, content_type=None):
            if self.prov.readonly:
                raise DAVError(FORBIDDEN, context_info="This vault is open read only.")
            self.buf = Capped()
            return self.buf

        def end_write(self, *, with_errors):
            if with_errors or self.buf is None:
                return
            data, self.buf = self.buf.getvalue(), None
            current = self.prov.entry(self.path)
            self.prov.do(journal.write, self.path, data, journal.etag(current) if current else "")

    class JunkFile(d["DAVNonCollection"]):
        """Finder's own bookkeeping files: in memory only, gone when the mount goes."""
        def __init__(self, path, environ, prov):
            super().__init__(path, environ)
            self.prov = prov

        def get_content_length(self):
            return len(self.prov.junk.get(self.path, b""))

        def get_content_type(self):
            return "application/octet-stream"

        def get_content(self):
            return io.BytesIO(self.prov.junk.get(self.path, b""))

        def get_etag(self):
            return None

        def support_etag(self):
            return False

        def get_last_modified(self):
            return time.time()

        def begin_write(self, *, content_type=None):
            self.buf = Capped()
            return self.buf

        def end_write(self, *, with_errors):
            if not with_errors:
                self.prov.junk[self.path] = self.buf.getvalue()

        def handle_delete(self):
            self.prov.junk.pop(self.path, None)
            return True

        def handle_move(self, dest_path):
            self.prov.junk[dest_path] = self.prov.junk.pop(self.path, b"")
            return True

        def handle_copy(self, dest_path, *, depth_infinity):
            self.prov.junk[dest_path] = self.prov.junk.get(self.path, b"")
            return True

        def delete(self):
            self.handle_delete()

        def copy_move_single(self, dest_path, *, is_move):
            raise DAVError(FORBIDDEN)

    return Provider()


def share_name(vault: str) -> str:
    """The volume's name in Finder: the vault's name, with only plain characters."""
    return re.sub(r"[^A-Za-z0-9 _.-]", "_", vault).strip(" .") or "Vault"


class Mount:
    def __init__(self, server, thread, port: int, share: str, secret: str, provider):
        self.server, self.thread, self.port, self.share = server, thread, port, share
        self.secret, self.provider = secret, provider
        self.where = ""

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/{self.secret}/v/"


def same_user(local_port: int, client_port: int, run=subprocess.run) -> bool:
    """Whether a connection to local_port (from client_port) comes from macOS's WebDAV mount agent
    (webdavfs_agent) run by this same Mac user: only the mount itself may talk to the server. The agent's
    processes are found by name and user (pgrep), then only their network connections are listed (lsof -p, never
    looking into mounted volumes, so it can't wait on this very server). Retried once; fails closed."""
    import os
    for attempt in range(2):
        try:
            pids = run(["pgrep", "-U", str(os.getuid()), "-x", "webdavfs_agent"], capture_output=True, text=True,
                       timeout=5).stdout.split()
            if pids:
                out = run(["lsof", "-b", "-w", "-nP", "-a", "-p", ",".join(pids), f"-iTCP@127.0.0.1:{client_port}",
                           "-Fn"], capture_output=True, text=True, timeout=5).stdout
                if f"n127.0.0.1:{client_port}->127.0.0.1:{local_port}" in out:
                    return True
        except Exception:
            pass
        if DEBUG:
            print("DAV same-user check failed", attempt, file=sys.stderr, flush=True)
        time.sleep(0.3)
    return False


def serve(session, journal, manager, on_read=None) -> Mount:
    """The WebDAV server for one open vault, on 127.0.0.1 and a free port (not mounted yet)."""
    import logging

    from cheroot import wsgi
    from wsgidav.wsgidav_app import WsgiDAVApp

    def silence():   # their messages can contain the secret address: never log them, at any level
        for name in ["wsgidav", "cheroot", *logging.root.manager.loggerDict]:
            if name.split(".")[0] in ("wsgidav", "cheroot"):
                lg = logging.getLogger(name)
                lg.disabled, lg.propagate = True, False
                lg.setLevel(logging.CRITICAL + 1)
                lg.handlers.clear()

    silence()

    secret = secrets.token_urlsafe(32)
    share = share_name(session.vault.name)
    provider = build_provider(session, journal, manager, session.read_only, on_read)
    config = {
        "host": "127.0.0.1", "port": 0,
        "provider_mapping": {f"/{secret}/v": provider},
        "simple_dc": {"user_mapping": {"*": True}},   # no login: the secret address and the same-user check guard it
        "verbose": 0, "logging": {"enable": False, "enable_loggers": []},
        "property_manager": True, "lock_storage": True,
        "dir_browser": {"enable": False},
        "add_header_MS_Author_Via": True,
    }
    class App(WsgiDAVApp):
        def resolve_provider(self, path):   # an exact match (the library only matches lowercase share names)
            root = f"/{secret}/v"
            if path == root or path.startswith(root + "/"):
                return root, provider
            return None, None

    app = App(config)
    silence()   # again: the library sets up its loggers while starting
    allowed: set[str] = set()

    class Gateway(wsgi.Gateway_10):   # hands each request its connection, so trust stays with that one socket
        def get_environ(self):
            env = super().get_environ()
            env["encryptor.conn"] = self.req.conn
            return env

    def guarded(environ, start_response):
        if DEBUG:
            print("DAV", environ.get("REQUEST_METHOD"), environ.get("PATH_INFO", "").replace(secret, "<secret>"),
                  environ.get("HTTP_HOST"), environ.get("REMOTE_PORT"), file=sys.stderr, flush=True)
        if environ.get("HTTP_HOST") not in allowed:
            start_response("421 Misdirected Request", [("Content-Type", "text/plain")])
            return [b"Wrong address."]
        path = environ.get("PATH_INFO", "")
        if not (path == f"/{secret}" or path.startswith(f"/{secret}/")):
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return [b"Not found."]
        # Checked once per connection (not per port: a port is reused by the next connection, which may be anyone's).
        conn = environ.get("encryptor.conn")
        if conn is None or not getattr(conn, "encryptor_same_user", False):
            client = int(environ.get("REMOTE_PORT") or 0)
            if conn is None or not same_user(port, client):
                if DEBUG:
                    print("DAV refused: not the same user", client, file=sys.stderr, flush=True)
                start_response("403 Forbidden", [("Content-Type", "text/plain")])
                return [b"Only programs of the Mac user who opened the vault can use it."]
            conn.encryptor_same_user = True
        return app(environ, start_response)

    server = wsgi.Server(("127.0.0.1", 0), guarded, numthreads=8, server_name="Encryptor")
    server.gateway = Gateway
    server.prepare()
    port = server.bind_addr[1]
    allowed.update({f"127.0.0.1:{port}", f"localhost:{port}"})
    thread = threading.Thread(target=server.serve, name="finder-mount", daemon=True)
    thread.start()
    return Mount(server, thread, port, share, secret, provider)


class Mounts:
    """The Finder mounts of open vaults, removed when a vault locks."""

    def __init__(self, manager, journal_for, base_dir, run=subprocess.run, on_read=None):
        self.on_read = on_read
        self.base_dir = base_dir            # mount points go here: <base_dir>/<vault name>
        self.manager = manager
        self.journal_for = journal_for      # session -> changes.Journal (the same one the AI's tools use)
        self.run = run
        self.active: dict[str, Mount] = {}
        self.mutex = threading.Lock()
        manager.on_lock.append(self.unmount)

    def available(self) -> bool:
        return sys.platform == "darwin" and shutil.which("mount_webdav") is not None

    def label(self) -> str:
        return "Finder"

    def where(self, vault: str) -> str:
        m = self.active.get(vault.casefold())
        return m.where if m else ""

    def mount(self, session) -> str:
        if not self.available():
            raise RuntimeError("Showing the vault in Finder works on a Mac only, for now.")
        with self.mutex:
            m = self.active.get(session.vault.name.casefold())
            if m is None:
                m = serve(session, self.journal_for(session), self.manager, self.on_read)
                point = self.base_dir / m.share
                point.mkdir(parents=True, exist_ok=True)
                # -S: no dialogs, and if this server goes away the volume is removed at once
                out = self.run(["mount_webdav", "-S", "-v", m.share, m.url, str(point)],
                               capture_output=True, text=True, timeout=90)
                m.where = self._find(m.port)
                if out.returncode != 0 or not m.where:
                    m.server.stop()
                    _rmdir(point)
                    raise RuntimeError("macOS didn't mount the vault. Try again, or use Browse files.")
                self.active[session.vault.name.casefold()] = m
                self.manager._event(session.vault.name, f"shown in Finder at {m.where}")
        self.run(["open", m.where], capture_output=True, timeout=30)
        return m.where

    def _find(self, port: int) -> str:
        out = self.run(["mount"], capture_output=True, text=True, timeout=30).stdout or ""
        for line in out.splitlines():
            if f"127.0.0.1:{port}/" in line:
                found = re.search(r" on (.+?) \(", line)
                if found:
                    return found.group(1)
        return ""

    def unmount(self, vault: str) -> None:
        with self.mutex:
            m = self.active.pop(vault.casefold(), None)
        if m is None:
            return
        if m.where:
            out = self.run(["diskutil", "unmount", m.where], capture_output=True, text=True, timeout=60)
            if out.returncode != 0:
                self.run(["diskutil", "unmount", "force", m.where], capture_output=True, text=True, timeout=60)
            if self._find(m.port):
                self.run(["umount", "-f", m.where], capture_output=True, text=True, timeout=60)
        m.server.stop()
        if m.where:
            _rmdir(Path(m.where))
        self.manager._event(vault, "removed from Finder")

    def unmount_all(self) -> None:
        for key in list(self.active):
            self.unmount(key)


def _rmdir(path: Path) -> None:
    """Remove an empty mount point folder (never anything with files in it)."""
    try:
        path.rmdir()
    except OSError:
        pass
