# SPDX-License-Identifier: AGPL-3.0-only
"""A native password box on the computer, for AI apps that can't open the unlock page by themselves.

macOS: AppleScript "display dialog ... with hidden answer". Linux: zenity, else kdialog. Windows: a PowerShell
masked prompt. The vault name, app and purpose are passed as separate arguments, never pasted into the script, so
nothing in them can change what runs. The password comes back to this program only; it is never logged.
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
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) and bool(
            shutil.which("zenity") or shutil.which("kdialog"))
    if sys.platform == "win32":
        return shutil.which("powershell") is not None
    return False


def password_box(vault: str, app: str, purpose: str, timeout: int = TIMEOUT, run=subprocess.run) -> str | None:
    """The password typed in a native box, or None when cancelled, timed out or unavailable."""
    vault, app, purpose = vault[:100], app[:80], purpose[:300]
    if sys.platform == "darwin":
        out = run(["osascript", "-e", MAC_SCRIPT, vault, app, purpose, str(timeout)],
                  capture_output=True, text=True, timeout=timeout + 30)
        text = (out.stdout or "").rstrip("\n")
        return text[3:] if out.returncode == 0 and text.startswith("OK:") else None
    if sys.platform.startswith("linux"):
        title = f"Encryptor: open {vault} for {app}"
        if shutil.which("zenity"):
            cmd = ["zenity", "--password", "--title", title, "--timeout", str(timeout)]
        else:
            cmd = ["kdialog", "--title", title, "--password", f"Type the password for {vault}. The AI never sees it."]
        out = run(cmd, capture_output=True, text=True, timeout=timeout + 30)
        return out.stdout.rstrip("\n") if out.returncode == 0 else None
    if sys.platform == "win32":
        ps = ("$p = Read-Host -AsSecureString ('Password for ' + $args[0]); "
              "[Runtime.InteropServices.Marshal]::PtrToStringUni([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))")
        out = run(["powershell", "-NoProfile", "-Command", ps, vault], capture_output=True, text=True, timeout=timeout + 30)
        return out.stdout.rstrip("\r\n") if out.returncode == 0 else None
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
    if sys.platform.startswith("linux"):
        text = f"{app} asks: {question}" + (f"\nWhy: {purpose}" if purpose else "")
        if shutil.which("zenity"):
            cmd = ["zenity", "--question", "--title", "Encryptor", "--text", text, "--ok-label", button,
                   "--cancel-label", "Cancel", "--default-cancel", "--timeout", str(timeout)]
        else:
            cmd = ["kdialog", "--title", "Encryptor", "--warningcontinuecancel", text, "--continue-label", button]
        return run(cmd, capture_output=True, text=True, timeout=timeout + 30).returncode == 0
    if sys.platform == "win32":
        ps = ("Add-Type -AssemblyName PresentationFramework; "
              "if ([System.Windows.MessageBox]::Show($args[0], 'Encryptor', 'OKCancel', 'Warning', 'Cancel') -eq 'OK') "
              "{ 'YES' } else { 'NO' }")
        out = run(["powershell", "-NoProfile", "-Command", ps, f"{app} asks: {question}"],
                  capture_output=True, text=True, timeout=timeout + 30)
        return out.stdout.strip() == "YES"
    return None
