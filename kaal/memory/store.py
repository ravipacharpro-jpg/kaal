"""Memory — SQLite sessions, auto-cleanup 30 din."""
import os, sqlite3, time

DB = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "sessions.db")

def _db():
    os.makedirs(os.path.dirname(os.path.abspath(DB)), exist_ok=True)
    c = sqlite3.connect(os.path.abspath(DB))
    c.execute("CREATE TABLE IF NOT EXISTS sessions(task TEXT, summary TEXT, ts REAL)")
    return c

def save(task, summary):
    c = _db()
    c.execute("INSERT INTO sessions VALUES(?,?,?)", (task[:300], summary[:500], time.time()))
    c.execute("DELETE FROM sessions WHERE ts < ?", (time.time() - 30*86400,))
    c.commit(); c.close()

def recent(n=5):
    c = _db()
    rows = c.execute("SELECT task,summary FROM sessions ORDER BY ts DESC LIMIT ?", (n,)).fetchall()
    c.close()
    return rows

def search(query, n=5):
    """Past sessions me keyword search (LIKE, local). Vector search nahi — zero-dep."""
    q = f"%{query[:80]}%"
    c = _db()
    rows = c.execute("SELECT task,summary FROM sessions WHERE task LIKE ? OR summary LIKE ?"
                     " ORDER BY ts DESC LIMIT ?", (q, q, n)).fetchall()
    c.close()
    return rows

def _tokens(s):
    import re
    return [w for w in re.findall(r"[a-z0-9]{2,}", s.lower()) if len(w) < 30]

def ranked_search(query, n=5):
    """TF-IDF cosine rank over past sessions — pure stdlib, zero-dep.
    LIKE se behtar: relevant purana context upar. Embeddings nahi, honest TF-IDF."""
    import math
    from collections import Counter
    c = _db()
    rows = c.execute("SELECT task,summary FROM sessions").fetchall()
    c.close()
    docs = [(t, s, _tokens(f"{t} {s}")) for t, s in rows]
    docs = [d for d in docs if d[2]]
    if not docs:
        return []
    q = _tokens(query)
    if not q:
        return []
    N = len(docs)
    df = Counter()
    for _, _, toks in docs:
        for w in set(toks):
            df[w] += 1
    idf = {w: math.log(1 + N / (1 + df[w])) for w in df}
    def vec(toks):
        tf = Counter(toks)
        return {w: (1 + math.log(tf[w])) * idf[w] for w in tf if w in idf}
    qv = vec(q)
    qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
    scored = []
    for t, s, toks in docs:
        dv = vec(toks)
        dot = sum(qv.get(w, 0.0) * dv.get(w, 0.0) for w in qv)
        dn = math.sqrt(sum(v * v for v in dv.values())) or 1.0
        sc = dot / (qn * dn)
        if sc > 0:
            scored.append((sc, t, s))
    scored.sort(reverse=True)
    return [(t, s) for _, t, s in scored[:n]]

def export_md(path="", n=20):
    """Session transcript markdown me (OpenCode share-style, local file)."""
    import datetime
    rows = recent(n)
    if not rows:
        return "Export ke liye koi session nahi"
    p = path or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
        f"kaal-export-{datetime.date.today().isoformat()}.md"))
    lines = ["# Kaal session export", ""]
    for t, s in reversed(rows):
        lines += [f"##  {t}", "", f"{s}", ""]
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines)[:50000])
    return f"Export ho gaya: {p}"
