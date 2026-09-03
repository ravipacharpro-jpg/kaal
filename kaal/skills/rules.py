"""Reusable agent skills — .md rule files, keyword pe brain prompt me load.
Claude-style: bar-bar wale complex kaam ke ready-to-use rules.
"""
import os, re

DIR = os.path.join(os.path.dirname(__file__), "rules")

BUILTIN = {
    "code-review.md": ("review, audit, check code, Code Review",
        "# Code Review skill\n- Pehle file_read se poora context lo\n- Bugs, security (secrets, injection), performance dekho\n- Fix file_edit se, har edit pe diff approval\n- Summary me file:line do"),
    "debug.md": ("debug, bug, fix, error, fail, test fail",
        "# Debug skill\n- Error message pura padho, file+line nikalo\n- file_read se aas-paas ka code dekho\n- Chhota fix -> file_edit + code_run se verify\n- Fail ho to 2 baar alag approach try karo, phir ruko"),
    "repo-scan.md": ("scan, codebase, poora project, structure",
        "# Repo Scan skill\n- repo_map se structure lo\n- Important files (README, config, main) file_read karo\n- Summary: stack + entry points + risk files"),
    "pr.md": ("pr, pull request, push, merge",
        "# PR skill\n- Pehle test_run se tests pass karo\n- gh CLI se branch + PR kholo\n- Summary me PR URL do"),
    "research.md": ("research, compare, best, vs, analysis",
        "# Research skill\n- browser_fetch se 2-3 sources padho\n- github_repo se stars/activity dekho\n- Table-style summary do, sources ke saath"),
}

def ensure():
    os.makedirs(DIR, exist_ok=True)
    for fn, (keys, body) in BUILTIN.items():
        p = os.path.join(DIR, fn)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"keywords: {keys}\n\n{body}\n")

def _dirs():
    """builtin + repo-local + global (OpenHands microagents style)."""
    ds = [DIR]
    ds.append(os.path.abspath(".kaal/skills"))
    ds.append(os.path.join(os.path.expanduser("~"), ".kaal", "skills"))
    return [d for d in ds if os.path.isdir(d)]

def match(task, limit=3):
    """Task se relevant skill bodies do. Repo-local skills ko priority."""
    ensure()
    t = task.lower()
    out = []
    for d in reversed(_dirs()):  # builtin pehle scan, local baad me (priority end me)
        try:
            files = sorted(os.listdir(d))
        except OSError:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            with open(os.path.join(d, fn), encoding="utf-8", errors="replace") as f:
                txt = f.read()
            m = re.search(r"keywords:\s*(.+)", txt)
            keys = [k.strip() for k in (m.group(1) if m else "").split(",")]
            tag = "local" if d != DIR else "builtin"
            if not keys:  # keywords nahi to hamesha load (repo instructions)
                out.append(f"## Skill [{tag}]: {fn}\n" + txt[:800])
            elif any(k and k in t for k in keys):
                out.append(f"## Skill [{tag}]: {fn}\n" + txt[:800])
            if len(out) >= limit:
                break
        if len(out) >= limit:
            break
    return "\n\n".join(out)
