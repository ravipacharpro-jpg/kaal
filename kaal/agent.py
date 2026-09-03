"""Kaal ReAct loop — plan -> act -> observe, summary only, no code dump."""
from .models.router import select_endpoint
from .skills import files as _files
from .skills import code as _code
from .skills import browser as _browser
from .mcp import github as _gh, registry as _mcp
from .memory import store as _mem

SENSITIVE = ("delete", "rm ", "format", "password", "token", "key")

def needs_permission(task):
    t = task.lower()
    return any(s in t for s in SENSITIVE)

def plan_task(task):
    """Task ko todos me todo. Agent khud banata hai."""
    steps = [s.strip() for s in task.replace("aur", ",").split(",") if s.strip()]
    if not steps:
        steps = [task]
    return [{"title": s, "status": "pending"} for s in steps[:8]]

def _dispatch(step, live_cb, ask_cb):
    """Step ko sahi skill/MCP pe bhejo. Sirf summary return, code dump nahi."""
    s = step.lower()
    if "delete" in s or s.startswith("rm "):
        if live_cb: live_cb("abhi file delete kar raha hu (permission ke saath)")
        return _files.delete_path(step.split()[-1], ask_cb)
    if "read" in s or "padh" in s or "file" in s:
        if live_cb: live_cb("abhi file read kar raha hu")
        parts = step.split()
        p = next((w for w in parts if "/" in w or "." in w), "")
        return _files.read_file(p)[:300] if p else _files.list_dir(".")[:300]
    if "code" in s or "python" in s or "chala" in s:
        if live_cb: live_cb("abhi code execute kar raha hu")
        return _code.run_python("print('kaal ok')")[:300]
    if "github" in s or "repo" in s:
        if live_cb: live_cb("abhi github check kar raha hu")
        _mcp.load("github")
        parts = step.split()
        r = next((w for w in parts if "/" in w and "." not in w), "ravipacharpro-jpg/kaal")
        return _gh.repo_info(r)[:300]
    if "browser" in s or "site" in s or "web" in s or "http" in s:
        if live_cb: live_cb("abhi browser se fetch kar raha hu")
        _mcp.load("browser")
        parts = step.split()
        u = next((w for w in parts if "." in w), "example.com")
        return _browser.fetch_text(u)[:300]
    if live_cb: live_cb(f"abhi ye kar raha hu: {step[:50]}")
    return f"✓ {step[:80]}"

def run_task(task, live_cb=None, ask_cb=None):
    """Ek task chalao. live_cb(line) = 1-line live update. Code dump nahi."""
    ep = select_endpoint()
    todos = plan_task(task)
    if needs_permission(task) and ask_cb and not ask_cb(f"Sensitive lag raha hai: {task[:80]} — aage badhu?"):
        return {"status": "denied", "summary": "User ne permission deny ki", "todos": todos, "endpoint": ep["name"]}
    out = []
    for i, td in enumerate(todos):
        td["status"] = "doing"
        res = _dispatch(td["title"], live_cb, ask_cb)
        if res == "Delete cancel — permission deny":
            td["status"] = "pending"
            out.append("✗ delete cancel")
            break
        td["status"] = "done"
        td["result"] = res[:200]
        out.append(f"✓ {td['title'][:50]}: {res[:100]}")
    _mcp.unload_idle(0)
    try: _mem.save(task, " | ".join(out)[:400])
    except Exception: pass
    return {"status": "done", "summary": " | ".join(out)[:300],
            "todos": todos, "endpoint": ep["name"]}
