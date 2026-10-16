# SPDX-License-Identifier: AGPL-3.0-only
"""A native password box (and an approval box) on a Mac, for AI apps that can't open the unlock page by themselves.

macOS only: AppleScript "display dialog ... with hidden answer". Everywhere else (Windows, Linux, servers, phones
through the web version) the unlock page and the link work in any browser, so nothing else is needed. The vault
name, app and purpose are passed as separate arguments, never pasted into the script, so nothing in them can
change what runs. The password comes back to this program only; it is never logged.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

TIMEOUT = 300   # seconds the box waits before giving up, like the unlock link

MAC_SCRIPT = """
on run argv
  set msg to "Your AI app " & item 2 of argv & " asks to open the vault " & quote & item 1 of argv & quote & "."
  if item 3 of argv is not "" then set msg to msg & return & "Why: " & item 3 of argv
  set msg to msg & return & return & "Type the vault password. The AI never sees it."
  try
    set r to display dialog msg default answer "" with hidden answer buttons {"Cancel", "Unlock"} ¬
      default button "Unlock" cancel button "Cancel" with title "Encryptor" with icon caution ¬
      giving up after (item 4 of argv as integer)
  on error number -128
    return "CANCEL:"
  end try
  if gave up of r then return "TIMEOUT:"
  return "OK:" & text returned of r
end run
"""


def available() -> bool:
    """Whether this computer can show a native password box (a desktop session, with the tool installed)."""
    if sys.platform == "darwin":
        return shutil.which("osascript") is not None
    return False


def password_box(vault: str, app: str, purpose: str, timeout: int = TIMEOUT, run=subprocess.run) -> str | None:
    """The password typed in a native box, or None when cancelled, timed out or unavailable."""
    vault, app, purpose = vault[:100], app[:80], purpose[:300]
    if sys.platform == "darwin":
        out = run(["osascript", "-e", MAC_SCRIPT, vault, app, purpose, str(timeout)],
                  capture_output=True, text=True, timeout=timeout + 30)
        text = (out.stdout or "").rstrip("\n")
        return text[3:] if out.returncode == 0 and text.startswith("OK:") else None
    return None


MAC_CONFIRM = """
on run argv
  set msg to "Your AI app " & item 2 of argv & " asks:" & return & return & item 1 of argv
  if item 3 of argv is not "" then set msg to msg & return & return & "Why: " & item 3 of argv
  try
    set r to display dialog msg buttons {"Cancel", item 4 of argv} default button "Cancel" cancel button "Cancel" ¬
      with title "Encryptor" with icon caution giving up after (item 5 of argv as integer)
  on error number -128
    return "NO"
  end try
  if gave up of r then return "NO"
  return "YES"
end run
"""


def confirm_box(question: str, app: str, purpose: str, button: str = "Allow", timeout: int = 120,
                run=subprocess.run) -> bool | None:
    """True when the person clicked the button, False when they said no or it timed out, None if unavailable.
    Cancel is the default button, so pressing Return never approves by accident."""
    question, app, purpose, button = question[:500], app[:80], purpose[:300], button[:40]
    if sys.platform == "darwin":
        out = run(["osascript", "-e", MAC_CONFIRM, question, app, purpose, button, str(timeout)],
                  capture_output=True, text=True, timeout=timeout + 30)
        return out.returncode == 0 and out.stdout.strip() == "YES"
    return None
