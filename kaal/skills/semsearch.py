"""Semantic-ish code search — SQLite FTS5 (BM25), zero deps, keyless.
Badi codebase me brain ko relevant snippets, poori file nahi.
"""
import os, sqlite3

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                  "memory", "search.db"))
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".nexus", "dist",
             "build", "memory", "logs"}
SKIP_EXT = {".png", ".jpg", ".db", ".pyc", ".bin", ".faiss"}

def _db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(path, chunk)")
    return c

def _chunks(text, n=12):
    lines = text.splitlines()
    for i in range(0, len(lines), n):
        yield "\n".join(lines[i:i + n]), i

def index_path(path, root="."):
    """Ek file ya folder index karo. Returns chunk count."""
    from .files import _safe
    base = _safe(root)
    if not base:
        return 0
    targets = []
    p = _safe(path) if not os.path.isabs(path) else os.path.abspath(path)
    if p and os.path.isfile(p):
        targets = [p]
    elif p and os.path.isdir(p):
        for dp, ds, fs in os.walk(p):
            ds[:] = [d for d in ds if d not in SKIP_DIRS]
            for fn in fs:
                if os.path.splitext(fn)[1] in SKIP_EXT:
                    continue
                fp = os.path.join(dp, fn)
                try:
                    if os.path.getsize(fp) < 200000:
                        targets.append(fp)
                except OSError:
                    pass
    c = _db()
    n = 0
    for fp in targets[:200]:
        try:
            with open(fp, encoding="utf-8", errors="replace") as f:
                txt = f.read(100000)
        except OSError:
            continue
        rel = os.path.relpath(fp, base)
        c.execute("DELETE FROM chunks WHERE path=?", (rel,))
        for chunk, ln in _chunks(txt):
            if chunk.strip():
                c.execute("INSERT INTO chunks VALUES(?,?)",
                          (f"{rel}#L{ln}", chunk[:2000]))
                n += 1
    c.commit()
    c.close()
    return n

def search(query, limit=5):
    """BM25 ranked snippets. Returns ['path#L: snippet']."""
    c = _db()
    try:
        rows = c.execute(
            "SELECT path, snippet(chunks, 1, '>>', '<<', '...', 20) FROM chunks "
            "WHERE chunks MATCH ? ORDER BY rank LIMIT ?", (query, limit)).fetchall()
    except Exception:
        rows = []
    c.close()
    return [f"{p}: {s[:300]}" for p, s in rows]
