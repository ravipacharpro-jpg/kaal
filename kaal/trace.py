"""Trace log — coze-loop style light observability.
Har run: task, mode, endpoint, tools, timing, budget. JSONL.
TUI /trace se recent dekho.
"""
import json, os, time

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                    "logs", "trace.jsonl"))

MAX_BYTES = 512 * 1024  # 512KB cap — unattended 24/7 me disk-fill guard
KEEP_TAIL = 200  # rotate pe akhri N lines rakho

def _rotate():
    """Cap cross to purani lines hatao (atomic replace). Fail-soft."""
    try:
        if not os.path.isfile(PATH) or os.path.getsize(PATH) <= MAX_BYTES:
            return
        with open(PATH, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        tail = lines[-KEEP_TAIL:]
        tmp = PATH + ".rot"
        with open(tmp, "w", encoding="utf-8") as f:
            f.writelines(tail)
        os.replace(tmp, PATH)
    except Exception:
        pass

def log(entry):
    try:
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        entry["ts"] = time.time()
        with open(PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry)[:2000] + "\n")
        _rotate()
    except Exception:
        pass

def recent(n=8):
    try:
        with open(PATH, encoding="utf-8") as f:
            lines = f.readlines()[-n:]
        return [json.loads(l) for l in lines]
    except Exception:
        return []

def warn(msg, where=""):
    """K-06: critical-path failures silently mat nigal — trace me warning likho.
    Secrets kabhi mat likho (msg already redacted hona chahiye)."""
    try:
        log({"kind": "warning", "where": str(where)[:80],
             "msg": str(msg)[:300]})
    except Exception:
        pass

def record_observation(run_id, tool, args, result, level):
    """Per-tool-call observation (claude-mem PostToolUse style)."""
    log({"kind": "observation", "run": run_id, "tool": tool,
         "level": level,
         "args": str(args)[:200],
         "result": str(result)[:300],
         "ts": time.time()})

def observations(run_id, n=20):
    try:
        with open(PATH, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f.readlines()[-n:]]
        return [r for r in rows if r.get("kind") == "observation" and r.get("run") == run_id]
    except Exception:
        return []
