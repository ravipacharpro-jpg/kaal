"""Bash runner — OpenInterpreter/ShellGPT style, strict allowlist + approval.
Dangerous commands hamesha block. Output truncate.
"""
import subprocess, shlex

ALLOW = {"ls", "pwd", "echo", "cat", "head", "tail", "wc", "date", "whoami",
         "git", "python3", "python", "pip", "pip3", "lsb_release", "uname",
         "df", "du", "find", "grep", "gh"}
BLOCK = ("rm -rf", "mkfs", "dd ", ":(){", "shutdown", "reboot", "> /dev/",
         "chmod 777", "curl |", "wget |")

def run(cmd, ask_cb=None, timeout=30):
    c = cmd.strip()[:500]
    if any(b in c for b in BLOCK):
        return "Block: dangerous command"
    try:
        import os as _os
        parts = shlex.split(c, posix=_os.name != "nt")
    except Exception:
        return "Command parse nahi hui"
    if not parts or parts[0] not in ALLOW:
        return f"Allowlist me nahi ({parts[0] if parts else '?'}). Allowed: ls git python3 gh ..."
    if ask_cb and not ask_cb(f"Bash chalau: {c[:100]}?"):
        return "Bash cancel — permission deny"
    try:
        r = subprocess.run(parts, capture_output=True, text=True, timeout=timeout)
        return ((r.stdout + r.stderr).strip() or f"Exit {r.returncode}")[:800]
    except subprocess.TimeoutExpired:
        return f"Timeout {timeout}s"
    except Exception as e:
        return f"Error: {e}"[:200]
