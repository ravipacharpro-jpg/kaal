"""Kaal brain — LLM tool-call loop (Claude-style ReAct).
Vault key ho to MODEL har step decide karta hai: socho -> tool call -> observe -> repeat.
Key nahi to brain inactive, legacy rule path chalta hai.
"""
import json, re
from ..skills import tools as _tools
from ..skills import rules as _rules
from ..agents.orchestrator import PERSONAS
from ..memory.store import recent as _recent
from ..memory.patterns import thread_context as _thread_ctx
from .router import try_chat

SYSTEM = ("Tum Kaal ho — autonomous coding agent. Hindi/Hinglish me jawab.\n"
          "Har jawab SIRF JSON me do, koi extra text nahi:\n"
          '{"thinking": "detail me: kya kar raha hu + kyun (2-4 lines ok)", '
          '"tool": {"name": "tool_name", "args": {...}}}  YA  '
          '{"thinking": "...", "tools": [{"name": "...", "args": {...}}]} (sirf independent READS ek saath)  YA  '
          '{"thinking": "...", "done": "final summary max 3 lines"}\n'
          "RULES: code TUI me mat dikhao, sirf summary. "
          "file_edit/file_delete/pr_open se pehle tool khud approval lega. "
          "Pehle file_read/repo_scan/file_outline se context lo, phir edit karo. "
          "Edit ke baad verify message dekho — fail to undo karke dobara. "
          "SELF-CORRECTION: tool error/fail aaye to wahi approach MAT dohrao — "
          "galti ka reason likho aur genuinely different approach lo (max 2 retry), "
          "phir bhi fail to done me rukawat + wajah likho. Max 10 steps me khatm karo.\n"
          "FEW-SHOT:\n"
          "TASK: README me version bump karo\n"
          '{"thinking": "pehle version line dhoondta hu", "tool": {"name": "file_read", "args": {"path": "README.md"}}}\n'
          "TOOL RESULT: ...version 0.1.0...\n"
          '{"thinking": "v0.1.0 mili L5 pe, 0.2.0 karta hu", "tool": {"name": "file_edit", "args": {"path": "README.md", "old": "0.1.0", "new": "0.2.0"}}}\n'
          "TASK: kaunsa project hai ye\n"
          '{"thinking": "markers check karta hu", "tool": {"name": "repo_scan", "args": {"path": "."}}}\n')

def _context(task):
    parts = []
    try:
        pa = "\n".join(f"- {k}: {v}" for k, v in PERSONAS.items())
        parts.append("SPECIALIST PERSONAS (tool results ko inki nazar se dekho):\n" + pa)
    except Exception:
        pass
    try:
        sk = _rules.match(task)
        if sk:
            parts.append("LOADED SKILLS:\n" + sk)
    except Exception:
        pass
    try:
        rows = _recent(3)
        if rows:
            parts.append("PAST TASKS:\n" + "\n".join(f"- {t[:60]} => {s[:100]}" for t, s in rows))
    except Exception:
        pass
    try:
        th = _thread_ctx()
        if th:
            parts.append(th)
    except Exception:
        pass
    return ("\n\n" + "\n\n".join(parts)) if parts else ""

def _parse_json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def _compress(msgs, keep_last=4):
    """Purane tool exchanges ko 1-line summary me sameto (context bloat guard).
    system + task + last N full, beech wale compressed."""
    if len(msgs) <= 2 + keep_last:
        return msgs
    head, tail = msgs[:2], msgs[-keep_last:]
    mid = []
    for m in msgs[2:-keep_last]:
        c = m.get("content", "")
        mid.append({"role": m.get("role", "user"),
                    "content": ("[old] " + c[:120])})
    return head + mid + tail

READONLY_TOOLS = {"file_read", "file_outline", "file_list", "browser_fetch",
                    "github_repo", "github_issues", "memory_recall", "repo_scan",
                    "code_search", "git_diff", "git_changelog"}

def _run_parallel(items, ask_cb, live_cb):
    """Independent read-only tools ek saath. Returns [(name, out)]."""
    from concurrent.futures import ThreadPoolExecutor

    def _one(t):
        spec = _tools.BY_NAME.get(t.get("name", ""))
        args = t.get("args", {}) if isinstance(t.get("args"), dict) else {}
        try:
            return spec["name"], str(spec["fn"](args))[:1200]
        except Exception as e:
            return t.get("name", "?"), f"Tool error: {e}"[:200]

    with ThreadPoolExecutor(max_workers=min(4, len(items))) as ex:
        return list(ex.map(_one, items))

def run(task, live_cb=None, ask_cb=None, max_iters=10, jobs=None, on_token=None):
    """LLM brain loop. Architect plan + editor execute (Aider style).
    jobs = smart-decomposed todos (LLM roles) display ke liye.
    on_token = streaming chunks (TUI live). Returns (todos, summary, endpoint)."""
    from .router import get_role_model, try_chat_stream
    editor = get_role_model("editor")
    plan_line = ""
    if jobs:
        plan_line = "\nPLAN (roles model ne diye): " + "; ".join(
            f"[{j['agent']}] {j['step'][:60]}" for j in jobs) + "\nIs plan pe chalo."
    msgs = [{"role": "system", "content": SYSTEM + _tools.spec_text() + _context(task)},
            {"role": "user", "content": f"TASK: {task}{plan_line}"}]
    todos = [{"title": j["step"][:50], "status": "pending",
              "agent": j["agent"]} for j in (jobs or [])]
    endpoint = "rule-based"
    for step in range(max_iters):
        msgs = _compress(msgs)
        buf = []
        def _stream(piece):
            buf.append(piece)
            if on_token:
                try:
                    on_token(piece)
                except Exception:
                    pass
            elif live_cb and len(buf) % 3 == 0:
                tail = "".join(buf)[-50:].replace("\n", " ")
                live_cb(f"💭 model likh raha hai: {tail}")
        name, txt = try_chat_stream(msgs, model=editor, on_token=_stream)
        if not txt:
            return todos, "", "rule-based"  # key fail — caller legacy pe jayega
        endpoint = name
        d = _parse_json(txt)
        if not d:
            msgs.append({"role": "assistant", "content": txt})
            msgs.append({"role": "user", "content": "Galat format. SIRF JSON do."})
            continue
        think = str(d.get("thinking", ""))[:500]
        if live_cb and think:
            live_cb(think[:80])
        if "done" in d:
            for td in todos:
                td["status"] = "done"
            todos.append({"title": task[:50], "status": "done",
                          "agent": "brain", "result": str(d["done"])[:200]})
            return todos, str(d["done"])[:400], endpoint
        if isinstance(d.get("tools"), list) and d["tools"]:
            items = d["tools"][:4]
            names = [t.get("name", "") for t in items]
            if all(n in READONLY_TOOLS for n in names):
                if live_cb:
                    live_cb(f"{len(items)} parallel reads: {', '.join(names)[:60]}")
                res = _run_parallel(items, ask_cb, live_cb)
                combined = "\n".join(f"[{n}]: {o[:400]}" for n, o in res)
                for n, o in res:
                    todos.append({"title": f"{n}: {think}"[:50], "status": "done",
                                  "agent": "brain", "result": o[:200]})
                msgs.append({"role": "assistant", "content": txt})
                msgs.append({"role": "user", "content": f"PARALLEL RESULTS:\n{combined}\nAgle step ka JSON do."})
                continue
            msgs.append({"role": "assistant", "content": txt})
            msgs.append({"role": "user", "content": "Parallel sirf read-only tools pe. Write wale alag-alag bhejo."})
            continue
        t = d.get("tool", {})
        spec = _tools.BY_NAME.get(t.get("name", ""))
        if not spec:
            msgs.append({"role": "assistant", "content": txt})
            msgs.append({"role": "user", "content": "Aisa tool nahi hai. List se chun ke dobara JSON do."})
            continue
        args = t.get("args", {}) if isinstance(t.get("args"), dict) else {}
        args["_ask"] = ask_cb
        try:
            out = str(spec["fn"](args))[:1200]
        except Exception as e:
            out = f"Tool error: {e}"[:200]
        todos.append({"title": f"{spec['name']}: {think}"[:50], "status": "done",
                      "agent": "brain", "result": out[:200]})
        msgs.append({"role": "assistant", "content": txt})
        msgs.append({"role": "user", "content": f"TOOL RESULT ({spec['name']}):\n{out}\nAgle step ka JSON do."})
    return todos, "Max steps — jitna hua summary: " + (todos[-1].get("result", "") if todos else "kuch nahi"), endpoint
