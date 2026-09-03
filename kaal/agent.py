"""Kaal ReAct loop — plan -> act -> observe, summary only, no code dump."""
from .models.router import select_endpoint

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

def run_task(task, live_cb=None, ask_cb=None):
    """Ek task chalao. live_cb(line) = 1-line live update. Code dump nahi."""
    ep = select_endpoint()
    todos = plan_task(task)
    if needs_permission(task) and ask_cb and not ask_cb(f"Sensitive lag raha hai: {task[:80]} — aage badhu?"):
        return {"status": "denied", "summary": "User ne permission deny ki", "todos": todos, "endpoint": ep["name"]}
    out = []
    for i, td in enumerate(todos):
        td["status"] = "doing"
        if live_cb:
            live_cb(f"abhi ye kar raha hu: {td['title'][:60]}")
        # yahan skill/MCP call lagega — abhi summary stub
        td["status"] = "done"
        out.append(f"✓ {td['title'][:60]}")
    return {"status": "done", "summary": " | ".join(out)[:300],
            "todos": todos, "endpoint": ep["name"]}
