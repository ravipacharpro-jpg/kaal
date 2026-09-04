"""Byte-prefix prompt cache — SHA-256(prompt+context+model), SQLite, zero token on hit.
Exact hit → stored response. TTL 24h, 500-row cap, 30d cleanup.
Router try_chat/try_llm me wired (economy.cache=false se off).
"""
import hashlib
import json
import os
import sqlite3
import time

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                  "memory", "promptcache.db"))
TTL = 24 * 3600
CAP = 500

SKILL = {"name": "promptcache", "desc": "LLM prompt cache (SHA-256, SQLite, TTL 24h)",
         "version": "0.1.0"}

def _db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS cache(hash TEXT PRIMARY KEY, prompt TEXT,"
              " response TEXT, tokens_saved INT, ts REAL)")
    return c

def _key(prompt, context="", model=""):
    h = hashlib.sha256()
    h.update(f"{model}\n{context}\n{prompt}".encode("utf-8", "replace"))
    return h.hexdigest()

def enabled():
    try:
        from .. import config_store as _cfg
        return bool(_cfg.get_all().get("economy", {}).get("cache", True))
    except Exception:
        return True

def lookup(prompt, context="", model=""):
    """(hit_bool, response). Expired/missing → (False, '')."""
    if not enabled():
        return False, ""
    try:
        c = _db()
        row = c.execute("SELECT response, ts FROM cache WHERE hash=?",
                        (_key(prompt, context, model),)).fetchone()
        c.close()
        if not row:
            return False, ""
        resp, ts = row
        if time.time() - ts > TTL:
            return False, ""
        return True, resp
    except Exception:
        return False, ""

def store(prompt, response, context="", model="", tokens_saved=0):
    try:
        c = _db()
        c.execute("INSERT OR REPLACE INTO cache VALUES(?,?,?,?,?)",
                  (_key(prompt, context, model), prompt[:2000], response[:8000],
                   int(tokens_saved), time.time()))
        c.execute("DELETE FROM cache WHERE ts < ?", (time.time() - 30 * 86400,))
        n = c.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        if n > CAP:
            c.execute("DELETE FROM cache WHERE hash IN (SELECT hash FROM cache"
                      " ORDER BY ts ASC LIMIT ?)", (n - CAP,))
        c.commit()
        c.close()
    except Exception:
        pass

def stats():
    """(rows, est_tokens_saved). /cache command ke liye."""
    try:
        c = _db()
        n, s = c.execute("SELECT COUNT(*), COALESCE(SUM(tokens_saved),0) FROM cache").fetchone()
        c.close()
        return int(n), int(s)
    except Exception:
        return 0, 0

def clear():
    try:
        c = _db()
        c.execute("DELETE FROM cache")
        c.commit()
        c.close()
        return "Cache clear"
    except Exception as e:
        return f"Cache clear fail: {e}"[:120]
