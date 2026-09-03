"""Human-readable memory — Hermes style MEMORY.md / USER.md.
Session-start pe brain prompt me inject. User khud edit kar sakta hai.
"""
import os

DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "memory"))

DEFAULT_MEMORY = """# MEMORY.md — Kaal ne ab tak kya seekha (auto + manual)
<!-- Kaal yahan successful patterns likhta hai. User edit kar sakta hai. -->
"""

DEFAULT_USER = """# USER.md — user ke baare me
<!-- Naam, pasand, project paths yahan likho. Kaal har session me padhta hai. -->
- Language: Hindi/Hinglish
"""


def _path(name):
    return os.path.join(DIR, name)


def ensure():
    os.makedirs(DIR, exist_ok=True)
    for fn, default in (("MEMORY.md", DEFAULT_MEMORY), ("USER.md", DEFAULT_USER)):
        p = _path(fn)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(default)


def read_all(max_chars=1500):
    ensure()
    out = []
    for fn in ("USER.md", "MEMORY.md"):
        try:
            with open(_path(fn), encoding="utf-8", errors="replace") as f:
                txt = f.read(max_chars)
            # comments hatao, content rakho
            lines = [l for l in txt.splitlines() if l.strip() and not l.strip().startswith("<!--")]
            if lines:
                out.append(f"{fn}:\n" + "\n".join(lines)[:max_chars // 2])
        except OSError:
            pass
    return "\n\n".join(out)


def append_memory(line):
    """Kaal khud seekhi baat likhta hai (dedupe basic)."""
    ensure()
    p = _path("MEMORY.md")
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            cur = f.read()
    except OSError:
        cur = ""
    line = line.strip()[:200]
    if line and line[:40] not in cur:
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n- {line}\n")
        return True
    return False
