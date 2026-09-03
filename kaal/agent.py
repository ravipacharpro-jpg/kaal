"""Kaal ReAct loop + multi-agent orchestrator + economy. Summary only, no code dump."""
from .models.router import select_endpoint, track_usage, budget_status, try_llm
from .skills import files as _files
from .skills import code as _code
from .skills import browser as _browser
from .mcp import github as _gh, registry as _mcp
from .memory import store as _mem
from .memory import patterns as _pat
from .agents.orchestrator import decompose

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

def run_task(task, live_cb=None, ask_cb=None, multi=None):
    """Ek task chalao. multi=True force multi-agent. live_cb = 1-line Hindi update."""
    ep = select_endpoint()
    jobs = decompose(task)
    use_multi = multi if multi is not None else len(jobs) > 1
    todos = [{"title": j["step"], "status": "pending", "agent": j["agent"]} for j in jobs]
    hint = ""
    try:
        hint = _pat.suggest(task)
        if hint and live_cb:
            live_cb("purana similar task mila — pattern use kar raha hu")
    except Exception:
        pass
    if needs_permission(task) and ask_cb and not ask_cb(f"Sensitive lag raha hai: {task[:80]} — aage badhu?"):
        return {"status": "denied", "summary": "User ne permission deny ki",
                "todos": todos, "endpoint": ep["name"], "mode": "single"}
    out = []
    for i, td in enumerate(todos):
        td["status"] = "doing"
        if live_cb and use_multi:
            live_cb(f"[{td['agent']}] abhi ye kar raha hu: {td['title'][:45]}")
        res = _dispatch(td["title"], live_cb if not use_multi else None, ask_cb)
        if use_multi and live_cb:
            pass  # live already shown with agent tag
        if res == "Delete cancel — permission deny":
            td["status"] = "pending"
            out.append("✗ delete cancel")
            break
        td["status"] = "done"
        td["result"] = res[:200]
        out.append(f"✓ [{td.get('agent','general')}] {td['title'][:40]}: {res[:80]}")
    _mcp.unload_idle(0)
    base = " | ".join(out)[:300]
    # Real LLM summary sirf tab jab user key hai, warna local summary (no-key safe)
    llm_note = ""
    try:
        name, txt = try_llm(f"Task: {task}\nResults: {base}\n1 line Hindi summary de.")
        if txt:
            llm_note = f" | 🧠 {txt[:150]}"
            ep = {"name": name, **ep} if isinstance(ep, dict) else ep
            ep["name"] = name
    except Exception:
        pass
    try:
        track_usage(ep["name"], 100 * max(1, len(todos)))
        _mem.save(task, base[:400])
        _pat.learn(task, base[:300])
    except Exception:
        pass
    b = budget_status()
    summ = (base + llm_note)[:400]
    if hint:
        summ = f"{hint[:150]} | " + summ
    return {"status": "done", "summary": summ,
            "todos": todos, "endpoint": ep["name"],
            "mode": "multi" if use_multi else "single",
            "budget": f"{b['used']}/5000 ({b['mode']})"}
