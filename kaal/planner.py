"""Plan mode — Plandex/Claude style: PLAN.md likho, approval lo, phir execute.
Bina key ke legacy decompose se plan, key ho to brain se.
"""
import os

PLAN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "PLAN.md"))

def write(task, steps):
    with open(PLAN, "w", encoding="utf-8") as f:
        f.write(f"# Plan: {task[:120]}\n\n")
        for i, s in enumerate(steps, 1):
            f.write(f"{i}. [ ] {s[:150]}\n")
    return PLAN

def read():
    try:
        with open(PLAN, encoding="utf-8") as f:
            return f.read()[:2000]
    except OSError:
        return ""

def draft(task, model=None):
    """Brain key ho to model se plan, warna decompose se."""
    try:
        from .models.router import brain_active, try_chat, get_role_model
        if brain_active():
            name, txt = try_chat([
                {"role": "system", "content": "Short numbered step plan de (max 6 steps), sirf steps, Hindi."},
                {"role": "user", "content": task[:500]}],
                model=model or get_role_model("architect"))
            if txt:
                steps = [l.strip("0123456789. )") for l in txt.splitlines() if l.strip()][:6]
                steps = [s for s in steps if s]
                if steps:
                    return steps
    except Exception:
        pass
    from .agents.orchestrator import decompose
    return [j["step"] for j in decompose(task)][:6] or [task]
