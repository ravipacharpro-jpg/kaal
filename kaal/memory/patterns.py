"""Pattern learning lite — no heavy deps. Successful tasks ke keywords save,
similar naye task pe purana summary suggest karo. Summary only.
"""
import os, json, re

PATS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "memory", "patterns.json"))
STOP = {"karo", "kar", "ke", "ki", "ka", "ko", "me", "se", "aur", "the", "a", "an", "do", "please"}

def _words(t):
    return {w for w in re.findall(r"[a-zA-Z\u0900-\u097F]{3,}", t.lower()) if w not in STOP}

def _load():
    try:
        with open(PATS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save(d):
    os.makedirs(os.path.dirname(PATS), exist_ok=True)
    with open(PATS, "w", encoding="utf-8") as f:
        json.dump(d[-100:], f, indent=2)

def learn(task, summary):
    d = _load()
    d.append({"task": task[:200], "summary": summary[:300], "words": sorted(_words(task))})
    _save(d)

def suggest(task):
    """Similar purana task mile to summary suggest karo, warna ''."""
    w = _words(task)
    if not w:
        return ""
    best, score = None, 0
    for p in _load():
        s = len(w & set(p.get("words", [])))
        if s > score:
            best, score = p, s
    if best and score >= 2:
        return f"💡 Pehle similar task: '{best['task'][:60]}' → {best['summary'][:120]}"
    return ""
