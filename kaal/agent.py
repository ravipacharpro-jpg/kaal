"""Kaal ReAct loop + multi-agent orchestrator + economy. Summary only, no code dump."""
from .models.router import select_endpoint, track_usage, budget_status, try_llm, brain_active
from .models.router import session_over, session_used, session_cap
from .models import brain as _brain
from .skills import files as _files
from .skills import code as _code
from .skills import browser as _browser
from .mcp import github as _gh, registry as _mcp
from .memory import store as _mem
from . import trace as _tr
from .memory import patterns as _pat
from .agents.orchestrator import decompose
from . import config_store as _cfg

SENSITIVE = {"delete_files": ("delete", "rm ", "format"),
             "code_execution": ("code", "python", "chala", "exec"),
             "browser": ("browser", "site", "web", "http", "github", "repo"),
             "secrets": ("password", "token", "key")}

def _self_review(task, summary):
    """Ek reviewer pass apne kaam pe. Returns ' |  review: ...' ya ''."""
    try:
        from .models.router import try_chat
        _, txt = try_chat([
            {"role": "system", "content": "Tum reviewer ho. Neeche task+result hai. "
             "Sirf 'OK' likho agar sahi hai, warna 1 line me kami batao (Hindi)."},
            {"role": "user", "content": f"TASK: {task[:300]}\nRESULT: {summary[:500]}"}])
        txt = (txt or "").strip()[:150]
        if not txt:
            return ""
        mark = "OK " if txt.upper().startswith("OK") else f"dhyaan do: {txt}"
        return f" |  review: {mark}"
    except Exception:
        return ""

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

def _dispatch(step, live_cb, ask_cb, level=None, run_id=None):
    """Step ko sahi skill/MCP pe bhejo. level=L1/L2/L3 (None = interactive prompts)."""
    from . import autonomy as _au
    import time as _t
    def _observe(tool, args, result):
        try:
            _tr.record_observation(run_id, tool, args, result, level)
        except Exception:
            pass
    s = step.lower()
    if "delete" in s or s.startswith("rm "):
        if live_cb: live_cb("abhi file delete kar raha hu (permission ke saath)")
        if level in ("L1", "L2"):
            ok, note = _au.tool_allowed("file_delete", level)
            if not ok:
                _observe("file_delete", step, note)
                return note
        _target = step.split()[-1]
        if not _cfg.check_perm(f"delete_files:{_target}",
                               ask_cb, f"Delete karu: {_target}?"):
            _observe("file_delete", step, "denied")
            return "Delete cancel — permission deny"
        res = _files.delete_path(step.split()[-1], lambda q: True)
        _observe("file_delete", step, res[:100]); return res
    if "read" in s or "padh" in s or "file" in s:
        if live_cb: live_cb("abhi file read kar raha hu")
        parts = step.split()
        p = next((w for w in parts if "/" in w or "." in w), "")
        res = _files.read_file(p)[:300] if p else _files.list_dir(".")[:300]
        _observe("file_read", step, res[:80]); return res
    if "code" in s or "python" in s or "chala" in s:
        if live_cb: live_cb("abhi code execute kar raha hu")
        if level in ("L1", "L2"):
            ok, note = _au.tool_allowed("code_run", level)
            if not ok:
                _observe("code_run", step, note); return note
        if not _cfg.check_perm("code_execution", ask_cb, "Code execute karu (sandbox, 30s)?"):
            _observe("code_run", step, "denied"); return "Code cancel — permission deny"
        res = _code.run_python("print('kaal ok')")[:300]
        _observe("code_run", step, res[:80]); return res
    if "github" in s or "repo" in s:
        if live_cb: live_cb("abhi github check kar raha hu")
        _mcp.load("github")
        parts = step.split()
        r = next((w for w in parts if "/" in w and "." not in w), "ravipacharpro-jpg/kaal")
        res = _gh.repo_info(r)[:300]
        _observe("github_repo", step, res[:80]); return res
    if "browser" in s or "site" in s or "web" in s or "http" in s:
        if live_cb: live_cb("abhi browser se fetch kar raha hu")
        _mcp.load("browser")
        parts = step.split()
        u = next((w for w in parts if "." in w), "example.com")
        res = _browser.fetch_text(u)[:300]
        _observe("browser_fetch", step, res[:80]); return res
    if live_cb: live_cb(f"abhi ye kar raha hu: {step[:50]}")
    _observe("generic", step, "done"); return f" {step[:80]}"

def run_task(task, live_cb=None, ask_cb=None, multi=None, on_token=None,
             ask_text_cb=None, level=None, step_cb=None, cancel=None, inbox=None):
    """Ek task chalao. Vault key ho to LLM BRAIN, nahi to legacy rule path.
    live_cb = 1-line Hindi update, on_token = streaming, ask_text_cb = clarification.
    step_cb(title, status) = live-todo hook (/bg). cancel = threading.Event.
    inbox = queue.Queue — legacy path me beech ke notes output me judte hain.
    Code dump nahi."""
    import time as _t
    _t0 = _t.time()
    _run_id = f"{int(_t0)}-{hash(task) & 0xFFFF}"
    from . import trace as _tr

    def _log(mode, ep, todos, status):
        try:
            tools = [t.get("title", "").split(":")[0] for t in todos]
            _tr.log({"task": task[:150], "mode": mode, "endpoint": ep,
                     "status": status, "steps": len(todos),
                     "tools": list(dict.fromkeys(tools))[:10],
                     "secs": round(_t.time() - _t0, 2), "level": level,
                     "run_id": _run_id})
        except Exception:
            pass

    def _observe(tool, args, result):
        try:
            _tr.record_observation(_run_id, tool, args, result, level)
        except Exception:
            pass
    # --- BRAIN PATH (Claude-style): model har step decide karta hai ---
    # Session cap cross to brain band (legacy-only) — budget burn guard
    _sess_over = session_over()
    if brain_active() and not _sess_over:
        if live_cb:
            live_cb("brain active — model soch raha hu")
        try:
            _files.checkpoint("brain-start")
        except Exception:
            pass
        try:
            jobs = decompose(task, smart=True)
            todos, summary, ep_name = _brain.run(task, live_cb, ask_cb, jobs=jobs,
                                                 on_token=on_token,
                                                 ask_text_cb=ask_text_cb, level=level,
                                                 step_cb=step_cb, cancel=cancel, inbox=inbox)
            if summary:  # brain ne complete kiya
                review_note = _self_review(task, summary)
                if review_note:
                    summary = (summary + review_note)[:450]
                try:
                    from . import autoskill as _ask2
                    skill = _ask2.maybe_distill(task, todos, ep_name)
                    if skill and live_cb:
                        live_cb(f" naya skill bana: {skill}")
                except Exception:
                    pass
                _mcp.unload_idle(0)
                daily, _p = _cfg.get_budget()
                try:
                    _mem.save(task, summary[:400])
                    _pat.learn(task, summary[:300])
                except Exception:
                    pass
                b = budget_status(daily)
                _log("brain", ep_name, todos, "done")
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
    if op and not _cfg.check_perm(op,
                                  ask_cb, f"Sensitive lag raha hai ({op}): {task[:70]} — aage badhu?"):
        _log("single", ep["name"], todos, "denied")
        return {"status": "denied", "summary": "User ne permission deny ki",
                "todos": todos, "endpoint": ep["name"], "mode": "single"}
    try:
        _files.checkpoint("task-start")
    except Exception:
        pass
    out = []

    def _one(td):
        if cancel is not None and cancel.is_set():
            td["status"] = "pending"
            return "cancelled", True
        td["status"] = "doing"
        if step_cb:
            try:
                step_cb(td["title"][:50], "doing")
            except Exception:
                pass
        res = _dispatch(td["title"], None, ask_cb, level, _run_id)
        if res == "Delete cancel — permission deny":
            td["status"] = "pending"
            return " delete cancel", True
        td["status"] = "done"
        td["result"] = res[:200]
        if step_cb:
            try:
                step_cb(td["title"][:50], "done")
            except Exception:
                pass
        return f" [{td.get('agent','general')}] {td['title'][:40]}: {res[:80]}", False

    risky = any(("delete" in t["title"].lower() or "edit" in t["title"].lower()
                 or "write" in t["title"].lower() or "commit" in t["title"].lower())
                for t in todos)
    try:
        from .platform_adapt import CONCURRENCY, detect as _plat
        workers = CONCURRENCY.get(_plat(), 1)
    except Exception:
        workers = 1
    if use_multi and workers > 1 and len(todos) > 1 and not risky:
        if live_cb:
            live_cb(f"{len(todos)} agents parallel chal rahe hain")
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(workers, len(todos))) as ex:
            results = list(ex.map(_one, todos))
        for line, stop in results:
            out.append(line)
            if stop:
                break
    else:
        for i, td in enumerate(todos):
            if cancel is not None and cancel.is_set():
                out.append("cancelled by user")
                break
            if inbox is not None:
                try:
                    while True:
                        note = inbox.get_nowait()
                        out.append(f" [note] {str(note)[:80]}")
                        if live_cb:
                            live_cb(f"note mila: {str(note)[:60]}")
                except Exception:
                    pass
            if live_cb and use_multi:
                live_cb(f"[{td['agent']}] abhi ye kar raha hu: {td['title'][:45]}")
            td["status"] = "doing"
            if step_cb:
                try:
                    step_cb(td["title"][:50], "doing")
                except Exception:
                    pass
            res = _dispatch(td["title"], live_cb if not use_multi else None, ask_cb, level, _run_id)
            if res == "Delete cancel — permission deny":
                td["status"] = "pending"
                out.append(" delete cancel")
                break
            td["status"] = "done"
            td["result"] = res[:200]
            if step_cb:
                try:
                    step_cb(td["title"][:50], "done")
                except Exception:
                    pass
            out.append(f" [{td.get('agent','general')}] {td['title'][:40]}: {res[:80]}")
    _mcp.unload_idle(0)
    base = " | ".join(out)[:300]
    # Auto-rollback: kuch bhi succeed nahi hua aur files chhui thin to wapas lao
    done_n = sum(1 for td in todos if td["status"] == "done")
    rollback_note = ""
    if done_n == 0 and out:
        try:
            rb = _files.rewind()
            if "files wapas" in rb and not rb.startswith("Rewind: 0"):
                rollback_note = f" | ↩ auto-rollback: {rb[:100]}"
        except Exception:
            pass
    # Real LLM summary sirf tab jab user key hai, warna local summary (no-key safe)
    llm_note = ""
    try:
        name, txt = try_llm(f"Task: {task}\nResults: {base}\n1 line Hindi summary de.")
        if txt:
            llm_note = f" |  {txt[:150]}"
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
    summ = (base + llm_note + rollback_note)[:450]
    if _sess_over:
        summ = f"[session cap {session_used()}/{session_cap()} — brain off, legacy] | " + summ
    if hint:
        summ = f"{hint[:150]} | " + summ
    _observe("run_complete", task, base[:150])
    _log("multi" if use_multi else "single", ep["name"], todos, "done")
    return {"status": "done", "summary": summ,
            "todos": todos, "endpoint": ep["name"],
            "mode": "multi" if use_multi else "single",
            "budget": f"{b['used']}/{daily} ({b['mode']})"}
