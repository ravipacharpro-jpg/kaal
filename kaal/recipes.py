"""Recipes — Goose style reusable workflows. recipes/*.md:
# name: <naam>
# steps:
# - step 1
# - step 2
"""
import os, re

DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recipes"))

BUILTIN = {
    "morning-review.md": ("# name: morning-review\n# steps:\n"
        "- git status dekho\n- git changelog 10 dikhao\n- due schedule jobs chalao\n"),
    "repo-health.md": ("# name: repo-health\n# steps:\n"
        "- repo scan karo\n- test chalao\n- summary me PASS/FAIL batao\n"),
    "quick-commit.md": ("# name: quick-commit\n# steps:\n"
        "- git diff dikhao\n- git commit karo\n"),
}

def ensure():
    os.makedirs(DIR, exist_ok=True)
    for fn, body in BUILTIN.items():
        p = os.path.join(DIR, fn)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(body)

def list_all():
    ensure()
    out = []
    for fn in sorted(os.listdir(DIR)):
        if fn.endswith(".md"):
            out.append(fn[:-3])
    return out

def get(name):
    ensure()
    p = os.path.join(DIR, name + ".md")
    try:
        with open(p, encoding="utf-8") as f:
            txt = f.read()
    except OSError:
        return []
    steps = [l.strip()[2:].strip() for l in txt.splitlines()
             if l.strip().startswith("- ")]
    return steps[:8]
