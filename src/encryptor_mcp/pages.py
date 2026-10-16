# SPDX-License-Identifier: AGPL-3.0-only
"""The unlock pages: plain HTML and CSS, no scripts, nothing loaded from elsewhere, every value escaped."""

from __future__ import annotations

import html

esc = html.escape

HEADERS = {
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
                               "frame-ancestors 'none'; base-uri 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}

CSS = """
:root{--ink:#14161f;--soft:#5a6072;--line:#d9dce6;--card:#fff;--page:#eef0f6;--brand:#2b3a67;--accent:#e0a526;
--ok:#16784a;--okbg:#e4f5ec;--err:#b42318;--errbg:#fdecea}
@media (prefers-color-scheme:dark){:root{--ink:#eceef6;--soft:#a3a9bd;--line:#353a4d;--card:#1a1d29;--page:#10121a;
--brand:#4a5f9e;--ok:#6fd49b;--okbg:#143022;--err:#ff8f80;--errbg:#3a1c1a}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:flex;align-items:flex-start;justify-content:center;padding:48px 16px;
background:var(--page);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{width:100%;max-width:440px;background:var(--card);border-radius:18px;overflow:hidden;
box-shadow:0 18px 40px -20px rgba(0,0,0,.35)}
header{background:var(--brand);color:#fff;padding:24px 26px}
header small{display:block;opacity:.8;font-weight:600;letter-spacing:.02em}
h1{margin:10px 0 4px;font-size:1.7rem;line-height:1.15}
header p{margin:0;opacity:.85}
section{padding:24px 26px}
label{display:block;font-weight:650;margin:0 0 8px}
input[type=password]{width:100%;font:inherit;padding:12px 14px;border-radius:10px;border:1.5px solid var(--line);
background:transparent;color:var(--ink)}
fieldset{border:0;padding:0;margin:18px 0 0}
legend{font-weight:650;margin-bottom:6px}
.choice{display:flex;gap:10px;align-items:center;font-weight:500;margin:6px 0}
.choice input{width:18px;height:18px;margin:0;accent-color:var(--brand)}
button{width:100%;margin-top:20px;font:inherit;font-weight:700;padding:13px;border:0;border-radius:10px;
background:var(--brand);color:#fff;cursor:pointer}
button.quiet{background:transparent;color:var(--err);border:1.5px solid var(--err)}
.msg{padding:11px 13px;border-radius:10px;font-weight:600;margin:0 0 16px}
.msg.err{background:var(--errbg);color:var(--err)}
.msg.ok{background:var(--okbg);color:var(--ok)}
.note{color:var(--soft);font-size:.92rem;margin:18px 0 0}
dl{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin:0}
dt{color:var(--soft)}dd{margin:0;font-weight:600}
footer{text-align:center;color:var(--soft);font-size:.82rem;padding:0 16px 18px}
"""

KEEP_LABELS = [("15m", "15 minutes"), ("1h", "1 hour"), ("lock", "Until I lock it"), ("app", "Until the AI app closes")]


def page(title: str, sub: str, body: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
            f'<title>{esc(title)} · Encryptor</title><style>{CSS}</style></head><body><main>'
            f'<header><small>Encryptor</small><h1>{esc(title)}</h1><p>{sub}</p></header>'
            f'<section>{body}</section></main></body></html>')


def unlock_form(code: str, vault: str, app: str, purpose: str, error: str = "", idle_minutes: int = 10) -> str:
    keep = "".join(f'<label class="choice"><input type="radio" name="keep" value="{v}"{" checked" if v == "lock" else ""}>'
                   f'{esc(t)}</label>' for v, t in KEEP_LABELS)
    body = ((f'<p class="msg err" role="alert">{esc(error)}</p>' if error else "")
            + '<dl>'
            + f'<dt>Vault</dt><dd>{esc(vault)}</dd><dt>Asked by</dt><dd>{esc(app)}</dd>'
            + (f'<dt>Why</dt><dd>{esc(purpose)}</dd>' if purpose else "")
            + '</dl>'
            + f'<form method="post" action="/unlock/{esc(code)}" style="margin-top:20px">'
            + '<label for="pw">Vault password</label>'
            + '<input id="pw" type="password" name="password" autocomplete="current-password" autofocus required>'
            + f'<fieldset><legend>Keep it open for</legend>{keep}</fieldset>'
            + '<fieldset><label class="choice"><input type="checkbox" name="read_only" value="yes">'
              'Open read only (the AI can look, not change)</label></fieldset>'
            + '<button type="submit">Unlock</button></form>'
            + f'<p class="note">The password stays on this computer: the AI never sees it. The vault also locks by itself '
              f'after {idle_minutes} minutes without use. Only continue if you asked your AI app for this just now.</p>')
    return page(f"Unlock {vault}", "Your AI app asks to open this vault.", body)


def unlocked(vault: str, status_code: str, read_only: bool, keep: str, app: str, ends_at: str,
             idle_minutes: int) -> str:
    keep_text = dict(KEEP_LABELS).get(keep, keep)
    body = (f'<p class="msg ok" role="status">Open{" (read only)" if read_only else ""}. You can close this page.</p>'
            f'<dl><dt>For</dt><dd>{esc(app)}</dd><dt>Kept open</dt><dd>{esc(keep_text)}</dd>'
            f'<dt>Locks at</dt><dd>{esc(ends_at)} at the latest</dd>'
            f'<dt>Without use</dt><dd>locks after {idle_minutes} minutes</dd></dl>'
            f'<form method="post" action="/vault/{esc(status_code)}/lock">'
            f'<button class="quiet" type="submit">Lock now</button></form>'
            f'<p class="note">To check later, open this page again. Bookmark it only on this computer.</p>')
    return page(f"{vault} is open", "Decrypted only in memory, on this computer.", body)


def message(title: str, text: str, ok: bool = False) -> str:
    return page(title, "", f'<p class="msg {"ok" if ok else "err"}">{esc(text)}</p>')
