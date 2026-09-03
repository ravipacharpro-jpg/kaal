"""Secret-leak scan — commit se pehle staged diff me API keys/tokens dhoondo.
NEXUS wala CodeQL/secret-scanning ka halka local version.
"""
import re

PATS = [
    ("AWS key", r"AKIA[0-9A-Z]{16}"),
    ("OpenAI key", r"sk-[A-Za-z0-9-_]{20,}"),
    ("Anthropic key", r"sk-ant-[A-Za-z0-9-_]{10,}"),
    ("GitHub token", r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    ("Generic secret", r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
    ("Private key", r"-----BEGIN (RSA )?PRIVATE KEY-----"),
    ("Bearer token", r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}"),
]

def scan_text(text):
    """Returns [issues]. Har issue: 'TYPE: snippet'."""
    out = []
    for name, pat in PATS:
        for m in re.finditer(pat, text):
            s = m.group(0)
            out.append(f"{name}: {s[:12]}...{s[-4:]}")
    return out

def scan_diff():
    """Staged diff scan karo. Returns (clean_bool, [issues])."""
    from .git import _git
    code, out = _git(["diff", "--cached"])
    if code != 0:
        code, out = _git(["diff"])
    issues = scan_text(out or "")
    return (len(issues) == 0), issues[:10]
