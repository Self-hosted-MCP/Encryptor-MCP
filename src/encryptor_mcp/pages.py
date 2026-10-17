# SPDX-License-Identifier: AGPL-3.0-only
"""The pages: plain HTML and CSS, no scripts, nothing loaded from elsewhere, every value escaped.

The look ("due-date card"): each vault is a ruled index card. While it's open it is lent to an AI app until a
time stamped in violet ink; its record (what changed, by whom) is written line by line on the card. One ink for
actions, one violet for stamps and focus, one red for what can't be undone. Light or dark follows the device.
"""

from __future__ import annotations

import contextvars
import html
import os
from urllib.parse import quote

esc = html.escape
NAME = "Encryptor MCP"
TAGLINE = "Encrypted vaults for your AI agents. You hold the keys."
THEME = contextvars.ContextVar("theme", default="light")   # this browser's choice (light unless switched), per request
HERE = contextvars.ContextVar("here", default="/")         # the page shown, so the theme switch can come back to it

HEADERS = {
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
                               "form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}

CONTRACT = """<!--
THESIS: a vault is a ruled index card lent to an AI app until a stamped time; refuses the shield-and-badge security dashboard.
OWN-WORLD: card stock with hairline blue rules and one red margin line, ink-black actions, violet date-stamp ink, red only for the irreversible.
STORY: the person sees what is open, until when, for which app, and what changed; unlocks, locks, undoes in one step.
FIRST VIEWPORT: one card; its title on the top rule, the violet stamp at right, the single primary action in ink below.
FORM: due-date card, list position 5, seed 0fff2009.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
-->"""

CSS = """
:root{
  --desk:#e7ebf1; --card:#fdfdfb; --rule:#d6e1ef; --lines:#e8eef6; --margin:#e3897d; --ink:#1b2130; --ink-2:#4d5566;
  --stamp:#4b3a8f; --stamp-soft:#ece8f7; --marker:#ffe27a; --marker-2:#e6defc; --red:#b5361f; --red-soft:#fbeae6; --line:#c9d2de;
  --shadow:0 1px 2px rgba(27,33,48,.06),0 8px 24px -12px rgba(27,33,48,.22);
}
:root[data-theme="dark"]{
  --desk:#10131a; --card:#191d27; --rule:#262c3a; --lines:#1f2430; --margin:#7a3b33; --ink:#eef1f6; --ink-2:#a9b1c1;
  --stamp:#b9a8f2; --stamp-soft:#272240; --marker:rgba(232,180,40,.42); --marker-2:rgba(150,125,240,.30); --red:#ff8a73; --red-soft:#3a1d18; --line:#323a4b;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 28px -14px rgba(0,0,0,.7);
}
.top .themes{margin:0;padding-left:20px;border-left:1.5px solid var(--line);display:flex}
.top .theme{display:inline-flex;align-items:center;gap:7px;background:none;border:0;padding:4px 0;cursor:pointer;
  font-family:inherit;font-size:1rem;font-weight:500;line-height:1.4;color:var(--ink-2)}
.top .theme:hover{color:var(--ink)}
.top .theme svg{width:18px;height:18px}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;background:var(--desk);color:var(--ink);
  font:16px/1.75 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif}
.top{max-width:var(--w,600px);margin:0 auto;padding:28px 20px 14px;display:flex;align-items:center;gap:12px 20px;
  flex-wrap:wrap}
.top .brand{margin-right:auto}
.brand{display:flex;align-items:center;gap:9px;color:var(--ink);text-decoration:none;font-weight:650;letter-spacing:-.01em}
.brand svg{width:22px;height:22px;color:var(--stamp);align-self:flex-start;margin-top:3px}
.brand > span{display:flex;flex-direction:column;line-height:1.3}
.brand small{font-weight:500;font-size:.8125rem;color:var(--ink-2);letter-spacing:0}
.top nav{display:flex;gap:22px;align-items:center;font-size:1rem;margin-left:auto;flex-wrap:wrap}
.top nav:empty{display:none}
.top nav a,.top nav button{color:var(--ink-2);font-weight:500;text-decoration:none;background:none;border:0;font-size:inherit;
  font-family:inherit;padding:4px 0;cursor:pointer;opacity:.85}
.top nav a:hover,.top nav button:hover{color:var(--ink);opacity:1}
.top nav a[aria-current]{color:var(--stamp);font-weight:650;opacity:1;text-decoration:underline;
  text-decoration-thickness:2px;text-underline-offset:6px}
main{max-width:var(--w,600px);margin:0 auto 56px;padding:0 20px}
.card{position:relative;background-color:var(--card);border-radius:4px;box-shadow:var(--shadow);
  padding:28px 26px 28px 58px;
  background-image:linear-gradient(90deg,transparent 41px,var(--margin) 41px,var(--margin) 42px,transparent 42px),
    repeating-linear-gradient(180deg,transparent 0,transparent 27px,var(--lines) 27px,var(--lines) 28px);
  background-position:0 0,0 0}
.card + .card{margin-top:22px}
h1{font-size:1.625rem;line-height:28px;letter-spacing:-.02em;margin:0 0 26.5px;padding:0;font-weight:700;
  text-wrap:balance;overflow-wrap:anywhere}
h1 .mark{padding:0 .18em;margin:0 -.1em;border-radius:.25em .6em .35em .5em;-webkit-box-decoration-break:clone;box-decoration-break:clone;background:linear-gradient(176deg,transparent 52%,var(--marker) 53%,var(--marker) 90%,transparent 91%)}
h2 .mark{padding:0 .2em;margin:0 -.12em;border-radius:.3em .55em .3em .5em;-webkit-box-decoration-break:clone;box-decoration-break:clone;background:linear-gradient(177deg,transparent 60%,var(--marker-2) 61%,var(--marker-2) 92%,transparent 93%)}
h2{font-size:1.25rem;line-height:28px;letter-spacing:-.01em;margin:28px 0 0;font-weight:700}
.card > h2:first-child{margin-top:0}
p{margin:0 0 10px}
.sub{color:var(--ink-2);margin:0;line-height:28px}
.headline{display:flex;gap:16px;align-items:flex-end;justify-content:space-between;margin-bottom:26.5px;
}
.headline h1{flex:1 1 0;min-width:0;margin:0;border-bottom:0}
.headline .stamp{margin:0 2px 5px 0}
.stamp{display:inline-block;flex:none;font:600 .8125rem/1.25 ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  letter-spacing:.08em;text-transform:uppercase;color:var(--stamp);border:1.5px solid var(--stamp);border-radius:3px;
  padding:5px 9px 4px;transform:rotate(-2deg);margin-top:6px;text-align:center;
  box-shadow:inset 0 0 0 2px var(--card),inset 0 0 0 3px var(--stamp)}
.stamp b{display:block;font-size:1.25rem;letter-spacing:.04em}
.stamp.mini{font-size:.8125rem;padding:2px 7px;margin:0 4px 0 0;box-shadow:none;letter-spacing:.06em}
.stamp.locked{color:var(--ink-2);border-color:var(--line);box-shadow:none;transform:none}
.facts{display:grid;grid-template-columns:auto 1fr;gap:0 18px;margin:0;line-height:28px}
.facts dt{color:var(--ink-2)}
.facts dd{margin:0;font-weight:600;overflow-wrap:anywhere}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;font-family:inherit;font-size:1rem;
  font-weight:600;line-height:1;padding:12px 18px;border-radius:4px;border:1.5px solid var(--ink);background:var(--ink);
  color:var(--card);text-decoration:none;cursor:pointer;min-height:44px;transition:background-color .15s,color .15s}
.btn:hover{background:transparent;color:var(--ink)}
.btn.plain{background:transparent;color:var(--ink)}
.btn.plain:hover{background:var(--ink);color:var(--card)}
.btn.red{background:transparent;border-color:var(--red);color:var(--red)}
.btn.red:hover{background:var(--red);color:var(--card)}
.btn.small{font-size:.8125rem;padding:7px 12px;min-height:36px}
.btn.wide{width:100%}
.btn svg{width:18px;height:18px;flex:none}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:28px}
.actions form{display:contents}
.link{color:var(--ink);font:inherit;background:none;border:0;padding:0;cursor:pointer;
  text-decoration:underline;text-decoration-color:var(--line);text-underline-offset:3px}
.link:hover{text-decoration-color:currentColor}
:focus-visible{outline:2.5px solid var(--stamp);outline-offset:2px}
label{display:block;font-weight:600;margin:28px 0 0;line-height:28px}
input[type=password],input[type=text],select{width:100%;font:inherit;color:var(--ink);
  background-color:transparent;border:0;border-bottom:1.5px solid var(--ink-2);border-radius:0;padding:6px 2px;min-height:44px}
input::placeholder{color:var(--ink-2);opacity:.75}
input[type=password]:focus,input[type=text]:focus,select:focus{outline:none;border-bottom-color:var(--stamp);
  box-shadow:0 1.5px 0 var(--stamp)}
select{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--ink-2) 50%),
  linear-gradient(135deg,var(--ink-2) 50%,transparent 50%);background-position:calc(100% - 14px) 52%,calc(100% - 9px) 52%;
  background-size:5px 5px;background-repeat:no-repeat;padding-right:28px}
select option{background:var(--card);color:var(--ink)}
fieldset{border:0;padding:0;margin:28px 0 0;min-width:0}
legend{font-weight:600;padding:0;margin:0;line-height:28px}
.seg{display:grid;grid-template-columns:repeat(4,1fr);border:1.5px solid var(--ink);border-radius:4px;overflow:hidden}
.seg label{position:relative;margin:0;font-weight:500;font-size:.8125rem;text-align:center;line-height:1.3;padding:10px 6px;
  cursor:pointer;border-left:1px solid var(--line);display:flex;align-items:center;justify-content:center;min-height:53px}
.seg label:first-of-type{border-left:0}
.seg input{position:absolute;opacity:0;width:1px;height:1px}
.seg label:has(input:checked){background:var(--ink);color:var(--card)}
.seg label:has(input:focus-visible){outline:2.5px solid var(--stamp);outline-offset:-5px}
.check{display:flex;gap:10px;align-items:flex-start;font-weight:500;margin:0;line-height:28px}
.check input{width:20px;height:20px;margin:4px 0 0;accent-color:var(--ink);flex:none}
.note{color:var(--ink-2);font-size:1rem;margin:28px 0 0;line-height:28px}
.msg{padding:14px;border-radius:4px;margin:0 0 28px;font-weight:600;line-height:28px}
.msg.err{background:var(--red-soft);color:var(--red)}
.msg.ok{background:var(--stamp-soft);color:var(--stamp)}
.rows{list-style:none;margin:0;padding:0}
.rows li{display:flex;gap:12px;align-items:center;min-height:56px;padding:0;box-shadow:inset 0 -1px 0 var(--rule)}
.rows li:last-child{box-shadow:none}
.rows.vaults li{padding:14px 0;box-shadow:none;border-bottom:1.5px dashed var(--line)}
.rows.vaults li:last-child{border-bottom:0}
.rows .main{flex:1;min-width:0}
.rows .name{font-weight:650;overflow-wrap:anywhere;line-height:28px}
.rows .meta{color:var(--ink-2);font-size:.8125rem;line-height:28px;overflow-wrap:anywhere}
.rows .meta.path,.facts .path{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rows .meta b{color:var(--stamp);font-weight:650}
.rows .acts{display:flex;gap:8px;flex:none;align-items:center}
.rows .acts form{margin:0}
.rows form{margin:0}
svg.kind{width:20px;height:20px;flex:none;color:var(--ink-2)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:7px;vertical-align:1px;
  border:1.5px solid var(--ink-2)}
.dot.on{background:var(--stamp);border-color:var(--stamp)}
.record{width:100%;border-collapse:collapse;font-size:1rem}
.record td{padding:0 10px 0 0;vertical-align:top;line-height:28px;box-shadow:inset 0 -1px 0 var(--rule)}
.record tr:last-child td{box-shadow:none}
.record .when{font:500 .8125rem/28px ui-monospace,"SF Mono",Menlo,Consolas,monospace;color:var(--stamp);white-space:nowrap}
.record .what{overflow-wrap:anywhere;width:100%}
.record .what small{display:block;color:var(--ink-2);font-size:.8125rem;line-height:28px}
.record td:last-child form{padding-top:10px}
.record .undone .act{text-decoration:line-through;color:var(--ink-2)}
.record td:last-child{padding-right:0;text-align:right}
.empty{color:var(--ink-2);margin:0;line-height:28px}
details{margin-top:12px}
summary{cursor:pointer;font-weight:600;color:var(--red);width:max-content;max-width:100%}
.crumbs{color:var(--ink-2);margin:0;line-height:28px;overflow-wrap:anywhere}
.crumbs a{color:var(--ink)}
.inline{display:flex;gap:8px;align-items:center}
.inline select{min-width:150px}
@media (max-width:560px){
  .card{padding:28px 16px 28px 40px;
    background-image:linear-gradient(90deg,transparent 27px,var(--margin) 27px,var(--margin) 28px,transparent 28px),
    repeating-linear-gradient(180deg,transparent 0,transparent 27px,var(--lines) 27px,var(--lines) 28px)}
  .top,main{padding-left:14px;padding-right:14px}
  .top{padding-top:18px}
  .top .brand{flex:1 1 0;min-width:0}
  .top .themes{order:2;border-left:0;padding-left:0;align-self:flex-start}
  .top nav{order:3;width:100%;margin-left:0;gap:18px}
  .seg{grid-template-columns:repeat(2,1fr)}
  .seg label:nth-of-type(3){border-left:0}
  .seg label:nth-of-type(n+3){border-top:1px solid var(--line)}
  .actions .btn{flex:1 1 auto}
  .rows li{flex-wrap:wrap}
  .rows .main{flex:1 1 170px}
  .rows .acts{flex:1 1 100%;padding-bottom:20px;flex-wrap:wrap;justify-content:flex-end;row-gap:10px}
  .inline{flex-wrap:wrap}
  .record,.record tbody,.record tr,.record td{display:block;width:auto}
  .record tr{position:relative;box-shadow:inset 0 -1px 0 var(--rule)}
  .record tr:last-child{box-shadow:none}
  .record td{border:0;padding:0;box-shadow:none}
  .record td:last-child{position:absolute;right:0;top:0}
  .record td:last-child form{padding-top:18px}
  .record tr:has(form) td.what{padding-right:76px}
}
"""

_SVG = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
ICONS = {
    "tag": f'<svg {_SVG} stroke-width="1.9"><path d="M3.5 10.6V4.5a1 1 0 0 1 1-1h6.1l9.7 9.7a1 1 0 0 1 0 1.4'
           'l-6.1 6.1a1 1 0 0 1-1.4 0z"/><circle cx="8" cy="8" r="1.6"/></svg>',
    "lock": f'<svg {_SVG} stroke-width="1.9"><rect x="5" y="10.5" width="14" height="10" rx="1.5"/>'
            '<path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/></svg>',
    "open": f'<svg {_SVG} stroke-width="1.9"><rect x="5" y="10.5" width="14" height="10" rx="1.5"/>'
            '<path d="M8 10.5V7.5a4 4 0 0 1 7.6-1.8"/></svg>',
    "folder": f'<svg class="kind" {_SVG} stroke-width="1.6"><path d="M3.5 7.5a1 1 0 0 1 1-1h5l2 2h8a1 1 0 0 1 1 1v8.5'
              'a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1z"/></svg>',
    "file": f'<svg class="kind" {_SVG} stroke-width="1.6"><path d="M6.5 3.5h7l4 4v12a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1'
            'v-15a1 1 0 0 1 1-1z"/><path d="M13.5 3.5v4h4"/></svg>',
    "moon": f'<svg {_SVG} stroke-width="1.8"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>',
    "sun": f'<svg {_SVG} stroke-width="1.8"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4'
           'M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4L6 18M18 6l1.4-1.4"/></svg>',
    "link": f'<svg class="kind" {_SVG} stroke-width="1.6"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/>'
            '<path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg>',
}

FAVICON = ("data:image/svg+xml," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#4b3a8f" stroke-width="2.2" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 10.6V4.5a1 1 0 0 1 1-1h6.1l9.7 9.7a1 1 0 0 1 0 1.4'
    'l-6.1 6.1a1 1 0 0 1-1.4 0z"/><circle cx="8" cy="8" r="1.6"/></svg>'))

KEEP_LABELS = [("15m", "15 minutes"), ("1h", "1 hour"), ("lock", "Until I lock it"), ("app", "Until the AI app closes")]
MODES = [("full", "Read and change"), ("read", "Read only"), ("hidden", "Hidden from AI")]


def theme_switch() -> str:
    """A no-script switch between light (the default) and dark, remembered by this browser."""
    dark = THEME.get() == "dark"
    label = "Light" if dark else "Dark"
    return (f'<form method="post" action="/theme" class="themes"><input type="hidden" name="next" value="{esc(HERE.get())}">'
            f'<button type="submit" class="theme" aria-label="Switch to {label.lower()} mode">'
            f'{ICONS["sun" if dark else "moon"]}{label}</button></form>')


def page(title: str, body: str, *, wide: bool = False, nav: str = "") -> str:
    width = ' style="--w:760px"' if wide else ""
    dark = THEME.get() == "dark"
    return (f'<!doctype html><html lang="en"{" data-theme=dark" if dark else ""}><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="robots" content="noindex"><meta name="color-scheme" content="{"dark" if dark else "light"}">'
            f'<link rel="icon" href="{FAVICON}">'
            f'<title>{esc(title)} · {NAME}</title><style>{CSS}</style></head><body{width}>{CONTRACT}'
            f'<header class="top"><span class="brand">{ICONS["tag"]}<span>{NAME}<small>{TAGLINE}</small></span></span><nav>{nav}</nav>{theme_switch()}</header>'
            f'<main>{body}</main></body></html>')


def center_nav(csrf: str = "", here: str = "") -> str:
    """Links of the control center, for a signed-in person."""
    links = [("/", "Vaults"), ("/settings", "Settings"), ("/activity", "Activity"), ("/about", "About")]
    out = "".join(f'<a href="{h}"{" aria-current=page" if h == here else ""}>{t}</a>' for h, t in links)
    if csrf:
        out += (f'<form method="post" action="/signout" style="margin:0"><input type="hidden" name="csrf" '
                f'value="{esc(csrf)}"><button type="submit">Sign out</button></form>')
    return out


def _msg(text: str, ok: bool = False) -> str:
    if not text:
        return ""
    return f'<p class="msg {"ok" if ok else "err"}" role="{"status" if ok else "alert"}">{esc(text)}</p>'


def _csrf(token: str) -> str:
    return f'<input type="hidden" name="csrf" value="{esc(token)}">'


# ---------------------------------------------------------------- unlocking

def unlock_form(code: str, vault: str, app: str, purpose: str, error: str = "", idle_minutes: int = 10,
                center: bool = False) -> str:
    keep = "".join(f'<label><input type="radio" name="keep" value="{v}"{" checked" if v == "lock" else ""}>'
                   f'<span>{esc(t)}</span></label>' for v, t in KEEP_LABELS)
    by_person = app.startswith("You")
    body = (f'<section class="card">{_msg(error)}'
            f'<div class="headline"><h1><span class="mark">Unlock {esc(vault)}</span></h1><span class="stamp locked">Locked</span></div>'
            + ("" if by_person else
               f'<dl class="facts"><dt>Asked by</dt><dd>{esc(app)}</dd>'
               + (f'<dt>Why</dt><dd>{esc(purpose)}</dd>' if purpose else "") + '</dl>')
            + f'<form method="post" action="/unlock/{esc(code)}">'
            '<label for="pw">Vault password</label>'
            '<input id="pw" type="password" name="password" autocomplete="current-password" autofocus required>'
            f'<fieldset><legend>Keep it open</legend><div class="seg">{keep}</div></fieldset>'
            '<label class="check"><input type="checkbox" name="read_only" value="yes">'
            '<span>Read only: the AI can look, not change</span></label>'
            f'<div class="actions"><button class="btn wide" type="submit">{ICONS["open"]}Unlock</button></div></form>'
            + ('<p class="note" style="text-align:center"><a class="link" href="/">Cancel</a></p>' if center else "")
            + f'<p class="note">The password stays here; the AI never sees it. Without use, the vault locks itself after '
            f'{idle_minutes} minutes.'
            + ("" if by_person else " Only continue if you asked your AI app for this just now.") + '</p></section>')
    return page(f"Unlock {vault}", body, nav='<a href="/">All vaults</a>' if center else "")


# ---------------------------------------------------------------- one open vault

def _action(a: str) -> str:
    return {"create": "Created", "write": "Changed", "append": "Added to", "mkdir": "New folder", "move": "Moved",
            "copy": "Copied to", "trash": "Trashed", "restore": "Restored", "undo": "Undid",
            "empty_trash": "Emptied the trash"}.get(a, a.capitalize())


def vault_page(v: dict) -> str:
    keep_text = dict(KEEP_LABELS).get(v["keep"], v["keep"])
    base = f'/vault/{esc(v["status_code"])}'
    finder = ""
    if v["finder"]:
        finder = (f'<form method="post" action="{base}/unmount"><button class="btn plain" type="submit">Remove from '
                  f'{esc(v["finder"])}</button></form>' if v["mounted"] else
                  f'<form method="post" action="{base}/mount"><button class="btn plain" type="submit">Show in '
                  f'{esc(v["finder"])}</button></form>')
    head = (f'<section class="card">{_msg(v["note"], ok=True)}'
            f'<div class="headline"><h1><span class="mark">{esc(v["name"])}</span></h1>'
            f'<span class="stamp" role="img" aria-label="Locks at {esc(v["ends_at"])} at the latest">'
            f'Due back<b>{esc(v["ends_at"])}</b></span></div>'
            f'<dl class="facts"><dt>Lent to</dt><dd>{esc(v["app"])}</dd>'
            f'<dt>Access</dt><dd>{"Read only" if v["read_only"] else "Read and change"}</dd>'
            f'<dt>Kept open</dt><dd>{esc(keep_text)}</dd>'
            f'<dt>Without use</dt><dd>locks after {v["idle_minutes"]} minutes</dd></dl>'
            f'<div class="actions"><a class="btn plain" href="{base}/files/">Browse files</a>{finder}'
            f'<form method="post" action="{base}/lock"><button class="btn" type="submit">{ICONS["lock"]}Lock now</button></form></div>'
            + (f'<p class="note">In {esc(v["finder"])} under Locations, decrypted only in memory. Deleting there '
               "puts things in the vault's trash.</p>" if v["mounted"] else
               '<p class="note">Decrypted only in memory, never on disk. You can close this page.</p>')
            + "</section>")
    if not v.get("center"):
        return page(v["name"], head)
    rows = []
    for c in v["changes"]:
        what = esc(c["path"]) + (f' → {esc(c["to"])}' if c["to"] else "")
        undo = (f'<form method="post" action="{base}/undo"><input type="hidden" name="change" value="{esc(c["id"])}">'
                f'<button class="btn small plain" type="submit">Undo</button></form>' if c["undoable"] else "")
        rows.append(f'<tr><td class="when">{esc(c["when"])}</td>'
                    f'<td class="what{" undone" if c["undone"] else ""}"><span class="act">{esc(_action(c["action"]))} {what}</span>'
                    f'<small>{esc(c["app"])}{(" · " + esc(c["purpose"])) if c["purpose"] else ""}'
                    f'{" · undone" if c["undone"] else ""}</small></td><td>{undo}</td></tr>')
    record = (f'<table class="record">{"".join(rows)}</table>' if rows else
              '<p class="empty">Nothing has changed yet.</p>')
    trash_rows = []
    for t in v["trash"]:
        restore = ("" if v["read_only"] else
                   f'<form method="post" action="{base}/undo"><input type="hidden" name="change" value="{esc(t["change"])}">'
                   f'<button class="btn small plain" type="submit">Restore</button></form>')
        trash_rows.append(f'<li>{ICONS["folder" if t["kind"] == "dir" else "file"]}<div class="main">'
                          f'<div class="name">{esc(t["path"])}</div><div class="meta">{esc(t["when"])} · {esc(t["app"])}</div>'
                          f'</div>{restore}</li>')
    if trash_rows:
        n = len(trash_rows)
        purge = ("" if v["read_only"] else
                 f'<details><summary>Delete the trash for good</summary><form method="post" action="{base}/purge">'
                 '<label class="check"><input type="checkbox" name="confirm" value="yes" required>'
                 f'<span>Delete {n} item{"s" if n != 1 else ""} for good. This can\'t be undone.</span></label>'
                 '<div class="actions"><button class="btn red" type="submit">Delete for good</button></div></form></details>')
        trash = f'<ul class="rows">{"".join(trash_rows)}</ul>{purge}'
    else:
        trash = '<p class="empty">The trash is empty.</p>'
    body = head + f'<section class="card"><h2><span class="mark">Record</span></h2>{record}<h2><span class="mark">Trash</span></h2>{trash}</section>'
    return page(v["name"], body, nav=f'<a href="{esc(v.get("center_link", "/"))}">All vaults</a>')


# ---------------------------------------------------------------- browsing

def browse(vault: str, status_code: str, folder: str, rows: list[tuple[str, str, str, str, bool]]) -> str:
    """rows: (name, kind, size, date, viewable). Links are built from the folder path, every part escaped."""
    base = f"/vault/{quote(status_code)}"
    parts = [p for p in folder.strip("/").split("/") if p]
    crumbs = [f'<a href="{base}/files/">{esc(vault)}</a>']
    for i, p in enumerate(parts):
        crumbs.append(f'<a href="{base}/files/{quote("/".join(parts[:i + 1]))}/">{esc(p)}</a>')
    out = []
    for name, kind, size, date, viewable in rows:
        rel = quote("/".join(parts + [name]))
        if kind == "dir":
            out.append(f'<li>{ICONS["folder"]}<div class="main"><a class="name link" href="{base}/files/{rel}/">{esc(name)}</a>'
                       f'<div class="meta">{esc(date)}</div></div></li>')
        elif kind == "link":
            out.append(f'<li>{ICONS["link"]}<div class="main"><div class="name">{esc(name)}</div>'
                       f'<div class="meta">link</div></div></li>')
        else:
            title = (f'<a class="name link" href="{base}/open/{rel}">{esc(name)}</a>' if viewable
                     else f'<div class="name">{esc(name)}</div>')
            out.append(f'<li>{ICONS["file"]}<div class="main">{title}<div class="meta">{esc(size)} · {esc(date)}</div></div>'
                       f'<a class="btn small plain" href="{base}/get/{rel}" aria-label="Download {esc(name)}">Download</a></li>')
    body = (f'<section class="card"><h1><span class="mark">{esc(parts[-1] if parts else vault)}</span></h1>'
            + (f'<p class="crumbs">{" / ".join(crumbs)}</p>' if parts else "")
            + (f'<ul class="rows">{"".join(out)}</ul>' if out else '<p class="empty">This folder is empty.</p>')
            + '<p class="note">Decrypted only in memory. Opened files show in this browser only; downloads are saved '
              'decrypted.</p></section>')
    return page(f"{vault}", body, wide=True, nav=f'<a href="{base}">Back to {esc(vault)}</a>')


# ---------------------------------------------------------------- the control center

def center_home(d: dict) -> str:
    rows = []
    for v in d["vaults"]:
        name = esc(v["name"])
        tag = {"read": " · the AI may only read", "hidden": " · hidden from the AI"}.get(v["mode"], "")
        if v["name"] == d.get("default"):
            tag += " · default"
        if v["open"]:
            meta = (f'<span class="dot on"></span>Lent to {esc(v["app"])}'
                    f'{" · read only" if v["read_only"] and v["mode"] != "read" else ""}{tag}')
            due = (f'<span class="stamp mini" role="img" aria-label="Due back {esc(v["ends_at"])}">'
                   f'Due {esc(v["ends_at"])}</span>')
            act = (due + f'<a class="btn small plain" href="/vault/{esc(v["status_code"])}">Open</a>'
                   f'<form method="post" action="/vaults/{quote(v["name"])}/lock">{_csrf(d["csrf"])}'
                   f'<button class="btn small" type="submit">Lock</button></form>')
        else:
            meta = f'<span class="dot"></span>Locked{tag}'
            act = (f'<form method="post" action="/vaults/{quote(v["name"])}/unlock">{_csrf(d["csrf"])}'
                   f'<button class="btn small" type="submit">Unlock</button></form>')
        act += f'<a class="btn small plain" href="/settings/vault/{quote(v["name"])}" aria-label="Settings for {name}">Settings</a>'
        rows.append(f'<li><div class="main"><div class="name">{name}</div><div class="meta">{meta}</div></div>'
                    f'<div class="acts">{act}</div></li>')
    vaults = (f'<ul class="rows vaults">{"".join(rows)}</ul>' if rows else
              '<p class="empty">No vaults yet. Add the folder of a Cryptomator vault to begin.</p>'
              '<div class="actions"><a class="btn" href="/settings#add">Add a vault</a></div>')
    apps = ""
    if d["hosted"]:
        items = []
        for a in d["apps"]:
            items.append(f'<li><div class="main"><div class="name">{esc(a["name"])}</div><div class="meta">'
                         f'{esc(", ".join(a["vaults"]) or "no vaults")} · {"may change files" if a["change"] else "read only"}'
                         f'</div></div><form method="post" action="/apps/{quote(a["id"])}/disconnect">{_csrf(d["csrf"])}'
                         f'<button class="btn small plain" type="submit">Disconnect</button></form></li>')
        apps = ('<section class="card"><h2><span class="mark">Connected AI apps</span></h2>'
                + (f'<ul class="rows">{"".join(items)}</ul>' if items else
                   '<p class="empty">None yet. Add this server to your AI app as a connector to begin.</p>')
                + "</section>")
    any_open = any(v["open"] for v in d["vaults"])
    actions = ""
    if rows:
        actions = ('<div class="actions"><a class="btn plain" href="/settings#add">Add a vault</a>'
                   + (f'<form method="post" action="/vaults/lock-all">{_csrf(d["csrf"])}'
                      f'<button class="btn" type="submit">{ICONS["lock"]}Lock all</button></form>' if any_open else "")
                   + '</div>')
    banner = ('<p class="msg ok" role="status">Read only for every AI app is on: they can read, not change. '
              '<a class="link" href="/settings#safety">Change</a></p>' if d.get("read_only_all") else "")
    body = (f'<section class="card">{_msg(d["note"], ok=True)}{banner}<h1><span class="mark">Your vaults</span></h1>{vaults}{actions}'
            '<p class="note">Ask your AI to find, read or update your files. You unlock, it works, and every vault '
            'locks again on its own.</p>'
            f'</section>{apps}')
    return page("Your vaults", body, wide=True, nav=center_nav(d["csrf"], "/"))


def _mode_form(v: dict, csrf: str, action: str) -> str:
    opts = "".join(f'<option value="{m}"{" selected" if m == v["mode"] else ""}>{t}</option>' for m, t in MODES)
    if v["mode_fixed"]:
        return f'<p class="meta">{esc(dict(MODES).get(v["mode"], v["mode"]))}, set in the setup file (ENCRYPTOR_MODES).</p>'
    return (f'<form method="post" action="{action}" class="inline">{_csrf(csrf)}'
            f'<input type="hidden" name="kind" value="mode"><input type="hidden" name="name" value="{esc(v["name"])}">'
            f'<select name="mode" aria-label="What the AI may do with {esc(v["name"])}">{opts}</select>'
            f'<button class="btn small plain" type="submit">Save</button></form>')


def _when(ts) -> str:
    import time as _t
    return _t.strftime("%d %b %H:%M", _t.localtime(ts)) if ts else ""


def _toggle(name: str, on: bool, label: str, disabled: bool = False) -> str:
    return (f'<label class="check"><input type="checkbox" name="{name}" value="yes"{" checked" if on else ""}'
            f'{" disabled" if disabled else ""}><span>{label}</span></label>')


def settings(d: dict) -> str:
    rows = []
    for v in d["vaults"]:
        extra = " · default" if v.get("default") else ""
        idle = f" · locks after {v['idle']} min" if v.get("idle") else ""
        rows.append(f'<li><div class="main"><div class="name">{esc(v["name"])}</div>'
                    f'<div class="meta">{esc(dict(MODES).get(v["mode"], v["mode"]))}{idle}{extra}</div></div>'
                    f'<div class="acts"><a class="btn small plain" href="/settings/vault/{quote(v["name"])}">Settings</a></div></li>')
    idle_opts = "".join(f'<option value="{n}"{" selected" if n == d["idle_minutes"] else ""}>{n} minutes</option>'
                        for n in (5, 10, 15, 30, 60))
    mode_opts = "".join(f'<option value="{m}">{t}</option>' for m, t in MODES)
    idle = (f'<p class="meta">{d["idle_minutes"]} minutes, set in the setup file.</p>' if d.get("idle_fixed") else
            f'<form method="post" action="/settings">{_csrf(d["csrf"])}<input type="hidden" name="kind" value="idle">'
            '<label for="idle" style="margin-top:0">Lock a vault after this long without use</label>'
            f'<div class="inline"><select id="idle" name="idle">{idle_opts}</select>'
            '<button class="btn plain" type="submit">Save</button></div></form>'
            '<p class="note" style="margin-top:0">A vault can have its own time in its settings.</p>')
    safety = (f'<form method="post" action="/settings">{_csrf(d["csrf"])}<input type="hidden" name="kind" value="safety">'
              + _toggle("read_only_all", d["read_only_all"],
                        "Read only for every AI app: they can read, but nothing can be changed"
                        + (" (set in the setup file)" if d["read_only_fixed"] else ""), d["read_only_fixed"])
              + _toggle("allow_purge", d["allow_purge"],
                        "AI apps may ask to delete the trash for good (you still approve each time)")
              + '<div class="actions"><button class="btn plain" type="submit">Save</button></div></form>')
    connect = (f'<section class="card"><h2><span class="mark">Connect an AI app</span></h2>'
               f'<p>Add this address to your AI app as a connector:</p><p class="meta"><b>{esc(d["mcp_url"])}</b></p>'
               '<p class="note" style="margin-top:0">You type your passphrase once and choose which vaults it may ask for.</p></section>'
               if d.get("mcp_url") else "")
    body = (f'{_msg(d["error"])}{_msg(d["note"], ok=True)}'
            '<section class="card"><h1><span class="mark">Settings</span></h1>'
            '<h2><span class="mark">Vaults</span></h2>'
            + (f'<ul class="rows vaults">{"".join(rows)}</ul>' if rows else '<p class="empty">No vaults yet.</p>')
            + '</section>'
            f'<section class="card" id="add"><h2><span class="mark">Add a vault</span></h2>'
            f'<form method="post" action="/settings">{_csrf(d["csrf"])}<input type="hidden" name="kind" value="add">'
            '<label for="vn" style="margin-top:0">Name</label>'
            '<input id="vn" type="text" name="name" required maxlength="60" placeholder="Taxes">'
            '<label for="vp">Vault folder</label><input id="vp" type="text" name="path" required '
            f'placeholder="{"/data/vaults/Taxes" if d["hosted"] else "~/Nextcloud/Taxes"}">'
            '<p class="note" style="margin-top:0">The folder that holds vault.cryptomator. Nothing is copied or moved.</p>'
            f'<label for="vm">The AI may</label><select id="vm" name="mode">{mode_opts}</select>'
            '<div class="actions"><button class="btn" type="submit">Add vault</button></div></form></section>'
            f'<section class="card"><h2><span class="mark">Auto-lock</span></h2>{idle}</section>'
            f'<section class="card" id="safety"><h2><span class="mark">Safety</span></h2>{safety}</section>'
            f'{connect}')
    return page("Settings", body, wide=True, nav=center_nav(d["csrf"], "/settings"))


def _devices_html(d: dict) -> str:
    dev_rows = []
    for dv in d.get("devices", []):
        who = esc(dv["agent"] or "A browser") + (" · this browser" if dv["this"] else "")
        meta = (f'Since {_when(dv["since"])} · last seen {_when(dv["seen"])}'
                + (f' · {esc(dv["ip"])}' if dv.get("ip") and dv["ip"] != "this computer" else "")
                + (" · remembered 90 days" if dv.get("remember") else ""))
        out = ("" if dv["this"] else
               f'<form method="post" action="/devices/{esc(dv["id"])}/signout">{_csrf(d["csrf"])}'
               f'<button class="btn small plain" type="submit">Sign out</button></form>')
        dev_rows.append(f'<li><div class="main"><div class="name">{who}</div><div class="meta">{meta}</div></div>{out}</li>')
    others = sum(1 for dv in d.get("devices", []) if not dv["this"])
    devices = (f'<ul class="rows">{"".join(dev_rows)}</ul>'
               + (f'<form method="post" action="/devices/others/signout">{_csrf(d["csrf"])}<div class="actions">'
                  '<button class="btn plain" type="submit">Sign out every other browser</button></div></form>' if others else ""))
    return devices


def _log_html(d: dict) -> str:
    log_rows = "".join(
        f'<tr><td class="when">{_when(e["time"])}</td><td class="what">{"Signed in" if e["ok"] else "Refused"}'
        f' · {esc(e["how"])}<small>{esc(e["agent"])}{(" · " + esc(e["ip"])) if e.get("ip") and e["ip"] != "this computer" else ""}'
        f'</small></td><td></td></tr>' for e in d.get("log", []))
    log = (f'<table class="record">{log_rows}</table>' if log_rows else '<p class="empty">No sign-ins yet.</p>')
    return log


def _about_html(d: dict) -> str:
    upd = d.get("update") or {}
    if upd.get("newer"):
        upd_line = (f'<p class="msg ok">Version {esc(upd["latest"])} is available. '
                    f'<a class="link" href="{esc(upd.get("url") or "https://github.com/" + d["repo"] + "/releases")}">What\'s new</a></p>')
    elif upd.get("error"):
        upd_line = f'<p class="meta">{esc(upd["error"])}</p>'
    elif upd.get("latest"):
        upd_line = '<p class="meta">You have the newest version.</p>'
    else:
        upd_line = ""
    repo = f'https://github.com/{d["repo"]}'
    about = (f'<dl class="facts"><dt>Version</dt><dd>{esc(d["version"])}</dd><dt>License</dt><dd>AGPL-3.0</dd></dl>'
             + upd_line
             + f'<form method="post" action="/about">{_csrf(d["csrf"])}<input type="hidden" name="kind" value="updates">'
             + _toggle("on", d["update_check"], "Check GitHub for a new version once a day (only the version number is asked)")
             + '<div class="actions"><button class="btn plain" type="submit">Save</button></form>'
             + f'<form method="post" action="/about">{_csrf(d["csrf"])}<input type="hidden" name="kind" value="check_now">'
               '<button class="btn plain" type="submit">Check now</button></form></div>'
             + '<h2><span class="mark">Help</span></h2>'
             + f'<ul class="rows"><li><div class="main"><a class="name link" href="{repo}">Source code</a>'
               '<div class="meta">Open source under the AGPL-3.0</div></div></li>'
             + f'<li><div class="main"><a class="name link" href="{repo}/issues/new">Report a problem or ask a question</a>'
               '<div class="meta">On GitHub</div></div></li>'
             + f'<li><div class="main"><a class="name link" href="{repo}/security/advisories/new">Report a security problem privately</a>'
               '<div class="meta">Only the maintainer sees it</div></div></li></ul>'
             + '<p class="note">Works with Cryptomator vaults. Not made by or affiliated with Cryptomator.</p>')
    return about


def activity(d: dict) -> str:
    """Signed-in browsers and the sign-in log: the person's own, never shown to AI apps."""
    devices, log = _devices_html(d), _log_html(d)
    body = (f'{_msg(d.get("note", ""), ok=True)}'
            '<section class="card"><h1><span class="mark">Activity</span></h1>'
            '<p class="msg ok">Private to you. Your AI apps can\'t see this page or these logs.</p>'
            f'<h2 id="devices"><span class="mark">Signed-in browsers</span></h2>{devices}</section>'
            f'<section class="card"><h2><span class="mark">Sign-ins, last 7 days</span></h2>{log}'
            '<p class="note">Kept on this computer or server only, for 7 days. Passphrases are never written down.</p>'
            '</section>')
    return page("Activity", body, wide=True, nav=center_nav(d["csrf"], "/activity"))


def about(d: dict) -> str:
    body = (f'{_msg(d.get("error", ""))}{_msg(d.get("note", ""), ok=True)}'
            '<section class="card"><h1><span class="mark">About</span></h1>'
            '<p>Encryptor MCP keeps your private files locked, and lets your AI help with them when you say so.</p>'
            '<p>You unlock a folder yourself. Then your AI can find, read and update files in it. Your password never '
            'goes to the AI, everything locks again on its own, and anything the AI changes can be undone.</p>'
            f'{_about_html(d)}</section>')
    return page("About", body, wide=True, nav=center_nav(d["csrf"], "/about"))


def vault_settings(d: dict) -> str:
    """One vault's settings: where it is, its format, what the AI may do, its own auto-lock, default, name, removal."""
    v = d["vault"]
    action = f'/settings/vault/{quote(v["name"])}'
    hidden = f'{_csrf(d["csrf"])}<input type="hidden" name="name" value="{esc(v["name"])}">'
    status = (f'Open, lent to {esc(d["app"])}. <a class="link" href="/vault/{esc(d["status_code"])}">Go to its page</a>'
              if d["open"] else "Locked")
    idle_opts = (f'<option value="all"{" selected" if not v.get("idle") else ""}>Same as all vaults ({d["idle_all"]} min)</option>'
                 + "".join(f'<option value="{n}"{" selected" if n == v.get("idle") else ""}>{n} minutes</option>'
                           for n in (5, 10, 15, 30, 60)))
    default = (f'<form method="post" action="{action}">{hidden}<input type="hidden" name="kind" value="default">'
               + _toggle("on", v.get("default"), "Default vault: the AI uses it when you don't name one")
               + '<div class="actions"><button class="btn plain" type="submit">Save</button></div></form>')
    place = (f'<form method="post" action="{action}">{hidden}<input type="hidden" name="kind" value="rename">'
             f'<label for="nn" style="margin-top:0">Name</label><div class="inline">'
             f'<input id="nn" type="text" name="new_name" required maxlength="60" value="{esc(v["name"])}">'
             '<button class="btn small plain" type="submit">Rename</button></div></form>'
             f'<form method="post" action="{action}">{hidden}<input type="hidden" name="kind" value="path">'
             f'<label for="np">Vault folder</label><div class="inline">'
             f'<input id="np" type="text" name="path" required value="{esc(home(v["path"]))}">'
             '<button class="btn small plain" type="submit">Change</button></div></form>'
             '<p class="note" style="margin-top:0">Renaming or moving locks the vault if it\'s open.</p>')
    remove = (f'<form method="post" action="{action}">{hidden}<input type="hidden" name="kind" value="remove">'
              '<p style="margin:0">Take it off this list. The vault and its files stay where they are, and AI apps '
              'can no longer ask for it.</p>'
              '<div class="actions"><button class="btn plain" type="submit">Remove from the list</button></div></form>')
    body = (f'{_msg(d["error"])}{_msg(d["note"], ok=True)}'
            f'<section class="card"><h1><span class="mark">{esc(v["name"])}</span></h1>'
            f'<dl class="facts"><dt>Status</dt><dd>{status}</dd>'
            f'<dt>Folder</dt><dd class="path" title="{esc(v["path"])}">{esc(home(v["path"]))}</dd>'
            f'<dt>Format</dt><dd>{esc(d["format"])}</dd></dl></section>'
            f'<section class="card"><h2><span class="mark">The AI may</span></h2>{_mode_form(v, d["csrf"], action)}'
            '<p class="note" style="margin-top:0">Hidden vaults never show to the AI; you can still open them here.</p>'
            f'{default}</section>'
            f'<section class="card"><h2><span class="mark">Auto-lock</span></h2>'
            f'<form method="post" action="{action}">{hidden}<input type="hidden" name="kind" value="vault_idle">'
            f'<label for="vi" style="margin-top:0">Lock it after this long without use</label>'
            f'<div class="inline"><select id="vi" name="idle">{idle_opts}</select>'
            '<button class="btn plain" type="submit">Save</button></div></form></section>'
            f'<section class="card"><h2><span class="mark">Name and folder</span></h2>{place}</section>'
            f'<section class="card"><h2><span class="mark">Remove</span></h2>{remove}</section>')
    return page(f"{v['name']} settings", body, wide=True, nav=center_nav(d["csrf"], "/settings"))


def confirm_change(d: dict) -> str:
    """The double check before a critical change: what will happen, then Yes or Cancel."""
    keep = "".join(f'<input type="hidden" name="{esc(k)}" value="{esc(v)}">' for k, v in d["fields"].items())
    facts = "".join(f'<dt>{esc(k)}</dt><dd class="path" title="{esc(v)}">{esc(v)}</dd>' for k, v in d.get("facts", []))
    body = ('<section class="card">'
            f'<h1><span class="mark">{esc(d["title"])}</span></h1>'
            + (f'<dl class="facts">{facts}</dl>' if facts else "")
            + "".join(f'<p>{esc(line)}</p>' for line in d["lines"])
            + f'<form method="post" action="{esc(d["action"])}">{_csrf(d["csrf"])}{keep}'
            '<input type="hidden" name="confirm" value="yes">'
            f'<div class="actions"><button class="btn" type="submit">{esc(d["button"])}</button>'
            f'<a class="btn plain" href="{esc(d["action"])}">Cancel</a></div></form></section>')
    return page(d["title"], body, nav=center_nav(d["csrf"], "/settings"))


def signin(hosted: bool, error: str = "") -> str:
    if hosted:
        body = (f'<section class="card">{_msg(error)}<h1><span class="mark">Sign in</span></h1>'
                '<form method="post" action="/signin"><label for="pp">Passphrase</label>'
                '<input id="pp" type="password" name="passphrase" autocomplete="current-password" autofocus required>'
                '<label class="check"><input type="checkbox" name="remember" value="yes">'
                '<span>Remember this browser for 90 days</span></label>'
                '<div class="actions"><button class="btn wide" type="submit">Sign in</button></div></form>'
                '<p class="note">The passphrase you set for this server. Five wrong tries pause sign-in for 15 minutes.</p>'
                '</section>')
    else:
        body = (f'<section class="card">{_msg(error)}<h1><span class="mark">Your vaults</span></h1>'
                '<p>Ask your AI app to open the Encryptor MCP control center. It opens here, in your own browser.</p>'
                '<p class="note">The page of a vault you just unlocked has a link here too. The link never goes through '
                'the chat.</p></section>')
    return page("Sign in", body)


def app_login(info: tuple[str, str] | None, req: str, vaults: list[str], error: str = "") -> str:
    if info is None:
        return message("Link expired", "This connection link expired. Start the connection again in your AI app.")
    app, back = info
    boxes = ("".join(f'<label class="check"><input type="checkbox" name="vault" value="{esc(n)}"><span>{esc(n)}</span></label>'
                     for n in vaults) or '<p class="empty">No vaults yet: add one on the control center first.</p>')
    body = (f'<section class="card">{_msg(error)}<h1><span class="mark">Connect {esc(app)}</span></h1>'
            f'<p class="sub">It returns to {esc(back)} afterwards.</p>'
            f'<form method="post" action="/login"><input type="hidden" name="req" value="{esc(req)}">'
            f'<fieldset><legend>Vaults it may ask for</legend>{boxes}</fieldset>'
            '<label class="check"><input type="checkbox" name="change" value="yes">'
            '<span>It may change files (every change can be undone)</span></label>'
            '<label for="pp">Passphrase</label>'
            '<input id="pp" type="password" name="passphrase" autocomplete="current-password" required>'
            '<div class="actions"><button class="btn wide" type="submit">Connect</button></div></form>'
            '<p class="note">Each vault still needs its own password whenever it opens. Connecting only lets the app ask.</p>'
            '</section>')
    return page(f"Connect {app}", body)


def message(title: str, text: str, ok: bool = False, center: bool = False) -> str:
    more = '<div class="actions"><a class="btn plain" href="/">All vaults</a></div>' if center else ""
    return page(title, f'<section class="card"><h1><span class="mark">{esc(title)}</span></h1>{_msg(text, ok)}{more}</section>')


def home(path: str) -> str:
    """A path for showing to the person, with the home folder as ~."""
    h = os.path.expanduser("~")
    return "~" + path[len(h):] if path.startswith(h + os.sep) else path
