"""Pattern learning — SQLite FTS5 (BM25) similarity, keyword-overlap nahi.
Same infra as code search. Thread continuity ke saath.
"""
import os, sqlite3, time

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                  "memory", "patterns.db"))
THREAD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                      "memory", "thread.json"))

def _db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS tasks USING fts5(task, summary)")
    return c

def learn(task, summary):
    c = _db()
    c.execute("INSERT INTO tasks VALUES(?,?)", (task[:300], summary[:500]))
    n = c.execute("SELECT count(*) FROM tasks").fetchone()[0]
    if n > 200:
        c.execute("DELETE FROM tasks WHERE rowid IN (SELECT rowid FROM tasks LIMIT ?)", (n - 200,))
    c.commit()
    c.close()
    _thread_append(task, summary)

def suggest(task, limit=2):
    """BM25 similar past tasks. Returns '' agar kuch nahi."""
    c = _db()
    try:
        words = [w for w in "".join(ch if ch.isalnum() else " " for ch in task).split() if len(w) > 2][:8]
        if not words:
            return ""
        q = " OR ".join(words)
        rows = c.execute(
            "SELECT task, summary FROM tasks WHERE tasks MATCH ? ORDER BY rank LIMIT ?",
            (q, limit)).fetchall()
    except Exception:
        rows = []
    c.close()
    if not rows:
        return ""
    return " Similar pehle: " + " | ".join(f"'{t[:50]}' → {s[:100]}" for t, s in rows)

def _thread_append(task, summary):
    import json
    try:
        with open(THREAD, encoding="utf-8") as f:
            th = json.load(f)
    except Exception:
        th = []
    th.append({"task": task[:200], "summary": summary[:300], "ts": time.time()})
    th = th[-6:]
    os.makedirs(os.path.dirname(THREAD), exist_ok=True)
    with open(THREAD, "w", encoding="utf-8") as f:
        json.dump(th, f)

def thread_context():
    """Last conversation thread (session continuity). Brain prompt me jata hai."""
    import json
    try:
        with open(THREAD, encoding="utf-8") as f:
            th = json.load(f)
    except Exception:
        return ""
    if not th:
        return ""
    lines = [f"- {e['task'][:80]} => {e['summary'][:120]}" for e in th[-4:]]
    return "THREAD (pichli baatein, 'pehle wala' isko refer karta hai):\n" + "\n".join(lines)
