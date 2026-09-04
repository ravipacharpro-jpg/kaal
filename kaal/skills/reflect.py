"""Cross-session reflections — session-end summary, next-session context.
memory/reflection_{date}.md + sessions.db reflections table (FTS-ish LIKE search).
Brain _context me akhri 3 auto-load (agent on_result hook se save hota hai —
LLM summary mile tabhi; legacy path me skip).
"""
import datetime
import os
import sqlite3
import time

SKILL = {"name": "reflect", "desc": "Cross-session reflection memory",
         "version": "0.1.0", "commands": ["/reflect"]}

def _db():
    from ..memory import store as _st
    dbp = os.path.abspath(os.path.join(os.path.dirname(_st.__file__), "sessions.db"))
    os.makedirs(os.path.dirname(dbp), exist_ok=True)
    c = sqlite3.connect(dbp)
    c.execute("CREATE TABLE IF NOT EXISTS reflections(text TEXT, ts REAL)")
    return c

def _md_path(date=None):
    d = date or datetime.date.today().isoformat()
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "memory", f"reflection_{d}.md"))

def save(text):
    """Reflection save karo (md + db). Returns path ya ''."""
    text = (text or "").strip()[:2000]
    if not text:
        return ""
    try:
        p = _md_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.datetime.now().isoformat(timespec='minutes')}\n{text}\n")
        c = _db()
        c.execute("INSERT INTO reflections VALUES(?,?)", (text, time.time()))
        c.execute("DELETE FROM reflections WHERE ts < ?", (time.time() - 90 * 86400,))
        c.commit()
        c.close()
        return p
    except Exception:
        return ""

def load_last(n=3):
    """Akhri N reflections (nayi pehle). Brain context ke liye."""
    try:
        c = _db()
        rows = c.execute("SELECT text FROM reflections ORDER BY ts DESC LIMIT ?",
                         (n,)).fetchall()
        c.close()
        return [r[0] for r in rows]
    except Exception:
        return []

def search(query, n=5):
    q = f"%{query[:80]}%"
    try:
        c = _db()
        rows = c.execute("SELECT text FROM reflections WHERE text LIKE ?"
                         " ORDER BY ts DESC LIMIT ?", (q, n)).fetchall()
        c.close()
        return [r[0] for r in rows]
    except Exception:
        return []

def build_reflection_prompt(task, summary):
    """LLM reflection prompt (pure, testable). English summary (spec)."""
    return ("Write a short reflection summary in English (5-8 lines): key decisions, "
            "errors made, patterns learned. No code.\n"
            f"TASK: {task[:300]}\nRESULT: {summary[:500]}")

def on_result(task, summary):
    """Skill hook — agent task-end pe. Substantive kaam ho + LLM mile to reflection.
    Chhote tasks skip (token bachao)."""
    try:
        from ..models.router import try_llm
        if not summary or len(summary) < 300 or len(task or "") < 20:
            return ""
        _, txt = try_llm(build_reflection_prompt(task, summary))
        if txt:
            p = save(txt[:1500])
            return f"reflection saved ({p})" if p else ""
    except Exception:
        pass
    return ""

SKILL["on_result"] = on_result
