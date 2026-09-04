"""Machine bridge — `--mode json` (single task) aur `--mode rpc` (ACP-style JSON-RPC over stdio).
IDE/tool integration ke liye: har line ek JSON request, har line ek JSON response.
Methods: initialize, session/new, prompt/run, session/list, shutdown.
Full ACP spec nahi — minimal, documented subset (README me saaf likha hai).
"""
import json, sys, time

METHODS = ("initialize", "session/new", "prompt/run", "session/list", "shutdown")

def _run_task(task):
    from .agent import run_task
    try:
        r = run_task(task, ask_cb=lambda q: False)
        return {"status": r.get("status", "done"), "summary": r.get("summary", "")[:500],
                "endpoint": r.get("endpoint", ""), "mode": r.get("mode", "")}
    except Exception as e:
        return {"status": "error", "summary": f"Error: {e}"[:200]}

def handle(req):
    """Pure handler — dict in, dict out. Testable bina stdio ke."""
    if not isinstance(req, dict):
        return {"error": "bad-request"}
    m = req.get("method", "")
    p = req.get("params", {}) or {}
    rid = req.get("id")
    if m == "initialize":
        return {"id": rid, "result": {"agent": "kaal", "version": "0.1.1-dev",
                                      "methods": list(METHODS)}}
    if m == "session/new":
        return {"id": rid, "result": {"session_id": f"s-{int(time.time())}"}}
    if m == "prompt/run":
        task = str(p.get("task", ""))[:2000]
        if not task:
            return {"id": rid, "error": "empty-task"}
        return {"id": rid, "result": _run_task(task)}
    if m == "session/list":
        try:
            from .memory.store import recent
            rows = recent(10)
            return {"id": rid, "result": [{"task": t[:80], "summary": s[:120]} for t, s in rows]}
        except Exception:
            return {"id": rid, "result": []}
    if m == "shutdown":
        return {"id": rid, "result": {"bye": True}}
    return {"id": rid, "error": f"unknown-method: {m}"}

def serve_stdio():
    """stdin lines → stdout lines. IDE (ACP-compatible harness) isko spawn kare."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            sys.stdout.write(json.dumps({"error": "bad-json"}) + "\n")
            sys.stdout.flush()
            continue
        res = handle(req)
        sys.stdout.write(json.dumps(res) + "\n")
        sys.stdout.flush()
        if req.get("method") == "shutdown":
            break

def run_json(task):
    """Single task → ek JSON object print (pip/tool friendly)."""
    sys.stdout.write(json.dumps({"task": task[:200], "result": _run_task(task)}) + "\n")
