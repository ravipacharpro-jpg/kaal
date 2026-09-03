"""Scheduler — jobs.json me task + interval_sec. run_due() se due jobs chalao.
Cron alternative: Termux me `termux-job-scheduler` ya simple loop se.
"""
import os, json, time

JOBS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "jobs.json"))

def _load():
    try:
        with open(JOBS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"jobs": []}

def _save(d):
    os.makedirs(os.path.dirname(JOBS), exist_ok=True)
    with open(JOBS, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)

def add(task, interval_sec=86400):
    d = _load()
    d["jobs"].append({"task": task[:200], "interval": interval_sec, "last": 0})
    _save(d)
    return f"Schedule ho gaya: '{task[:50]}' har {interval_sec}s"

def due():
    d = _load()
    now = time.time()
    return [j for j in d["jobs"] if now - j.get("last", 0) >= j.get("interval", 86400)]

def mark_done(task):
    d = _load()
    for j in d["jobs"]:
        if j["task"] == task:
            j["last"] = time.time()
    _save(d)

def run_due(run_fn, level=None):
    """Due jobs ko run_fn(task, level) se chalao. level None = caller decide.
    Har run schedule.log me (dresnite/loops style ls/logs). Returns summaries."""
    out = []
    for j in due():
        try:
            r = run_fn(j["task"], level)
        except TypeError:
            r = run_fn(j["task"])
        line = f"⏰ [{level or '-'}] {j['task'][:60]}: {str(r)[:120]}"
        out.append(line)
        _log_run(j["task"], str(r)[:200])
        mark_done(j["task"])
    return out if out else ["Koi due job nahi"]

def _log_path():
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "schedule.log"))

def _log_run(task, summary):
    import time
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%m-%d %H:%M')} | {task[:80]} | {summary[:100]}\n")
    except Exception:
        pass

def log_tail(n=8):
    try:
        with open(_log_path(), encoding="utf-8") as f:
            return f.readlines()[-n:]
    except Exception:
        return []

def list_jobs():
    return _load().get("jobs", [])

def remove(idx):
    d = _load()
    try:
        j = d["jobs"].pop(int(idx))
        _save(d)
        return f"Hataya: {j['task'][:60]}"
    except (IndexError, ValueError):
        return "Galat number"
