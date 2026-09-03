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

def match(task):
    """Task se relevant skill bodies do (max 2)."""
    ensure()
    t = task.lower()
    out = []
    for fn in sorted(os.listdir(DIR)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(DIR, fn), encoding="utf-8", errors="replace") as f:
            txt = f.read()
        m = re.search(r"keywords:\s*(.+)", txt)
        keys = [k.strip() for k in (m.group(1) if m else "").split(",")]
        if any(k and k in t for k in keys):
            out.append(f"## Skill: {fn}\n" + txt[:800])
        if len(out) >= 2:
            break
    return "\n\n".join(out)
