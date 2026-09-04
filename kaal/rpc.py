"""Machine bridge — `--mode json` (single task) aur `--mode rpc` (ACP-style JSON-RPC over stdio).
IDE/tool integration ke liye: har line ek JSON request, har line ek JSON response.
Methods: initialize, session/new, prompt/run, prompt/stream, session/cancel,
session/list, fs/readTextFile, fs/writeTextFile, availableCommands, shutdown.
Full ACP spec nahi — extended documented subset (README me saaf likha hai).
prompt/* worker threads me chalte hain taaki session/cancel beech me aa sake.
"""
import json, queue, sys, threading, time

METHODS = ("initialize", "session/new", "prompt/run", "prompt/stream",
           "session/cancel", "session/interject", "session/list",
           "fs/readTextFile", "fs/writeTextFile", "availableCommands", "shutdown")

_SESSIONS = {}
_SLOCK = threading.Lock()

def _new_session():
    sid = f"s-{int(time.time() * 1000)}"
    with _SLOCK:
        _SESSIONS[sid] = {"cancel": threading.Event(), "inbox": queue.Queue()}
    return sid

def _run_task(task, cancel=None, inbox=None, on_token=None):
    from .agent import run_task
    try:
        r = run_task(task, ask_cb=lambda q: False, cancel=cancel, inbox=inbox,
                     on_token=on_token)
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
        return {"id": rid, "result": {"agent": "kaal", "version": "0.6.0",
                                      "methods": list(METHODS)}}
    if m == "session/new":
        return {"id": rid, "result": {"session_id": _new_session()}}
    if m == "prompt/run":
        task = str(p.get("task", ""))[:2000]
        if not task:
            return {"id": rid, "error": "empty-task"}
        sid = p.get("session_id")
        if sid is not None:  # K-01: supplied session bind karo, unknown reject
            with _SLOCK:
                s = _SESSIONS.get(str(sid))
            if not s:
                return {"id": rid, "error": f"unknown-session: {sid}"}
            return {"id": rid, "result": _run_task(task, cancel=s["cancel"],
                                                   inbox=s["inbox"])}
        return {"id": rid, "result": _run_task(task)}
    if m == "session/cancel":
        sid = str(p.get("session_id", ""))
        with _SLOCK:
            s = _SESSIONS.get(sid)
        if not s:
            return {"id": rid, "error": f"unknown-session: {sid}"}
        s["cancel"].set()
        return {"id": rid, "result": {"cancelled": sid}}
    if m == "session/interject":
        sid = str(p.get("session_id", ""))
        note = str(p.get("note", ""))[:300]
        with _SLOCK:
            s = _SESSIONS.get(sid)
        if not s:
            return {"id": rid, "error": f"unknown-session: {sid}"}
        if note:
            s["inbox"].put(note)
        return {"id": rid, "result": {"noted": True}}
    if m == "fs/readTextFile":
        try:
            from .skills import files as _f
            return {"id": rid, "result": {"text": _f.read_file(str(p.get("path", "")))[:8000]}}
        except Exception as e:
            return {"id": rid, "error": f"read fail: {e}"[:150]}
    if m == "fs/writeTextFile":
        if p.get("approve") is not True:
            return {"id": rid, "error": "approve:true chahiye (destructive op)"}
        try:
            from .skills import files as _f2
            return {"id": rid, "result": {"msg": _f2.write_file(
                str(p.get("path", "")), str(p.get("content", "")))[:300]}}
        except Exception as e:
            return {"id": rid, "error": f"write fail: {e}"[:150]}
    if m == "availableCommands":
        try:
            from .tui import palette as _pal
            return {"id": rid, "result": [{"cmd": c, "desc": d} for c, d, _o in _pal.COMMANDS]}
        except Exception:
            return {"id": rid, "result": []}
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
    """stdin lines → stdout lines. prompt/* worker threads me (cancel beech me).
    Streaming chunks event-lines ke roop me aate hain (same id)."""
    from concurrent.futures import ThreadPoolExecutor
    out_lock = threading.Lock()

    def emit(obj):
        with out_lock:
            sys.stdout.write(json.dumps(obj) + "\n")
            sys.stdout.flush()

    def do_stream(rid, task, session_id=None):
        if session_id is not None:
            with _SLOCK:
                s = _SESSIONS.get(str(session_id))
            if not s:
                emit({"id": rid, "error": f"unknown-session: {session_id}"})
                return
            sid, temp = str(session_id), False
        else:
            sid = _new_session()
            temp = True
            with _SLOCK:
                s = _SESSIONS[sid]
        emit({"id": rid, "result": {"session_id": sid, "streaming": True}})

        def _tok(piece):
            emit({"id": rid, "event": "chunk", "text": str(piece)[:300]})

        res = _run_task(task, cancel=s["cancel"], inbox=s["inbox"], on_token=_tok)
        emit({"id": rid, "event": "done", "result": res})
        if temp:
            with _SLOCK:
                _SESSIONS.pop(sid, None)

    def do_run(rid, task):
        emit({"id": rid, "result": _run_task(task)})

    with ThreadPoolExecutor(max_workers=4) as ex:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except Exception:
                emit({"error": "bad-json"})
                continue
            m = req.get("method", "") if isinstance(req, dict) else ""
            if m == "prompt/stream":
                task = str((req.get("params") or {}).get("task", ""))[:2000]
                if not task:
                    emit({"id": req.get("id"), "error": "empty-task"})
                    continue
                ex.submit(do_stream, req.get("id"), task,
                          (req.get("params") or {}).get("session_id"))
                continue
            if m == "prompt/run":
                task = str((req.get("params") or {}).get("task", ""))[:2000]
                if not task:
                    emit({"id": req.get("id"), "error": "empty-task"})
                    continue
                fut = ex.submit(do_run, req.get("id"), task)
                if req.get("params", {}).get("wait", True):
                    fut.result()
                continue
            res = handle(req)
            emit(res)
            if m == "shutdown":
                break

def run_json(task):
    """Single task → ek JSON object print (pip/tool friendly)."""
    sys.stdout.write(json.dumps({"task": task[:200], "result": _run_task(task)}) + "\n")
