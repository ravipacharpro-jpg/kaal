"""Kaal brain — LLM tool-call loop (Claude-style ReAct).
Vault key ho to MODEL har step decide karta hai: socho -> tool call -> observe -> repeat.
Key nahi to brain inactive, legacy rule path chalta hai.
"""
import json, re
from ..skills import tools as _tools
from ..skills import rules as _rules
from ..agents.orchestrator import PERSONAS
from ..memory.store import recent as _recent
from .router import try_chat

SYSTEM = ("Tum Kaal ho — autonomous coding agent. Hindi/Hinglish me jawab.\n"
          "Har jawab SIRF JSON me do, koi extra text nahi:\n"
          '{"thinking": "1 line me abhi kya kar raha hu", '
          '"tool": {"name": "tool_name", "args": {...}}}  YA  '
          '{"thinking": "...", "done": "final summary max 3 lines"}\n'
          "RULES: code TUI me mat dikhao, sirf summary. "
          "file_edit/file_delete se pehle soch me approval mango (tool khud puchega). "
          "Pehle file_read/repo_scan se context lo, phir edit karo. "
          "SELF-CORRECTION: tool error/fail aaye to galti note karke 2 baar alag approach try karo, "
          "phir bhi fail to done me rukawat + wajah likho. Max 10 steps me khatm karo.\n")

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
    return ("\n\n" + "\n\n".join(parts)) if parts else ""

def _parse_json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def run(task, live_cb=None, ask_cb=None, max_iters=10):
    """LLM brain loop. Architect plan + editor execute (Aider style).
    Returns (todos, summary, endpoint)."""
    from .router import get_role_model
    editor = get_role_model("editor")
    msgs = [{"role": "system", "content": SYSTEM + _tools.spec_text() + _context(task)},
            {"role": "user", "content": f"TASK: {task}"}]
    todos, endpoint = [], "rule-based"
    for step in range(max_iters):
        name, txt = try_chat(msgs, model=editor)
        if not txt:
            return todos, "", "rule-based"  # key fail — caller legacy pe jayega
        endpoint = name
        d = _parse_json(txt)
        if not d:
            msgs.append({"role": "assistant", "content": txt})
            msgs.append({"role": "user", "content": "Galat format. SIRF JSON do."})
            continue
        think = str(d.get("thinking", ""))[:80]
        if live_cb and think:
            live_cb(think)
        if "done" in d:
            todos.append({"title": task[:50], "status": "done",
                          "agent": "brain", "result": str(d["done"])[:200]})
            return todos, str(d["done"])[:400], endpoint
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
