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
