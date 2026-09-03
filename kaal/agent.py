"""Kaal ReAct loop + multi-agent orchestrator + economy. Summary only, no code dump."""
from .models.router import select_endpoint, track_usage, budget_status, try_llm, has_keys
from .models import brain as _brain
from .skills import files as _files
from .skills import code as _code
from .skills import browser as _browser
from .mcp import github as _gh, registry as _mcp
from .memory import store as _mem
from .memory import patterns as _pat
from .agents.orchestrator import decompose
from . import config_store as _cfg

SENSITIVE = {"delete_files": ("delete", "rm ", "format"),
             "code_execution": ("code", "python", "chala", "exec"),
             "browser": ("browser", "site", "web", "http", "github", "repo"),
             "secrets": ("password", "token", "key")}

def needs_permission(task):
    t = task.lower()
    for op, keys in SENSITIVE.items():
        if any(s in t for s in keys):
            return op
    return ""

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
        if not _cfg.check_perm("delete_files", ask_cb, f"Delete karu: {step.split()[-1]}?"):
            return "Delete cancel — permission deny"
        return _files.delete_path(step.split()[-1], lambda q: True)
    if "read" in s or "padh" in s or "file" in s:
        if live_cb: live_cb("abhi file read kar raha hu")
        parts = step.split()
        p = next((w for w in parts if "/" in w or "." in w), "")
        return _files.read_file(p)[:300] if p else _files.list_dir(".")[:300]
    if "code" in s or "python" in s or "chala" in s:
        if live_cb: live_cb("abhi code execute kar raha hu")
        if not _cfg.check_perm("code_execution", ask_cb, "Code execute karu (sandbox, 30s)?"):
            return "Code cancel — permission deny"
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
    """Ek task chalao. Vault key ho to LLM BRAIN, nahi to legacy rule path.
    live_cb = 1-line Hindi update. Code dump nahi."""
    # --- BRAIN PATH (Claude-style): model har step decide karta hai ---
    if has_keys():
        if live_cb:
            live_cb("brain active — model soch raha hu")
        try:
            _files.checkpoint("brain-start")
        except Exception:
            pass
        try:
            todos, summary, ep_name = _brain.run(task, live_cb, ask_cb)
            if summary:  # brain ne complete kiya
                _mcp.unload_idle(0)
                daily, _p = _cfg.get_budget()
                try:
                    _mem.save(task, summary[:400])
                    _pat.learn(task, summary[:300])
                except Exception:
                    pass
                b = budget_status(daily)
                return {"status": "done", "summary": summary[:400],
                        "todos": todos or [{"title": task[:50], "status": "done", "agent": "brain"}],
                        "endpoint": ep_name, "mode": "brain",
                        "budget": f"{b['used']}/{daily} ({b['mode']})"}
        except Exception:
            pass  # gir gaya to legacy path
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
    op = needs_permission(task)
    if op and not _cfg.check_perm(op if op != "secrets" else "delete_files",
                                  ask_cb, f"Sensitive lag raha hai ({op}): {task[:70]} — aage badhu?"):
        return {"status": "denied", "summary": "User ne permission deny ki",
                "todos": todos, "endpoint": ep["name"], "mode": "single"}
    try:
        _files.checkpoint("task-start")
    except Exception:
        pass
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
    daily, _per = _cfg.get_budget()
    b = budget_status(daily)
    summ = (base + llm_note)[:400]
    if hint:
        summ = f"{hint[:150]} | " + summ
    return {"status": "done", "summary": summ,
            "todos": todos, "endpoint": ep["name"],
            "mode": "multi" if use_multi else "single",
            "budget": f"{b['used']}/{daily} ({b['mode']})"}
