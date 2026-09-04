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
