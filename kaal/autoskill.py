"""Auto-skill — solved task se reusable recipe banao (compounding agent).
Brain path me, >=3 distinct tools use hue to model procedure distill karta hai.
Code nahi, recipe steps save hote hain (safe) + MEMORY.md me 1 line.
"""
import os, re

def _slug(task):
    s = re.sub(r"[^a-z0-9]+", "-", task.lower()).strip("-")[:30] or "task"
    return s

def maybe_distill(task, todos, endpoint):
    """Returns recipe name ya ''. Sirf brain-success + 3+ distinct tools pe."""
    try:
        from .models.router import try_chat, get_role_model
        from . import recipes as _rc
        from .memory.persona import append_memory
    except Exception:
        return ""
    tools = {t.get("title", "").split(":")[0] for t in todos if t.get("agent") == "brain"}
    tools.discard("")
    if len(tools) < 3:
        return ""
    try:
        from . import config_store as _cfg
        if not _cfg.get_all().get("model", {}).get("auto_skill", True):
            return ""
    except Exception:
        pass
    try:
        _, txt = try_chat([
            {"role": "system", "content": "Neeche ek solved task ke steps hain. "
             "Reusable procedure ko 3-6 generic steps me likho (ek per line, '- ' se shuru). "
             "Sirf steps, koi extra text nahi."},
            {"role": "user", "content": f"TASK: {task[:200]}\nSTEPS:\n" + "\n".join(
                f"- {t.get('title','')[:80]}" for t in todos[:10])}],
            model=get_role_model("architect"))
        steps = [l.strip()[2:].strip() for l in (txt or "").splitlines()
                 if l.strip().startswith("- ")][:6]
        if len(steps) < 2:
            return ""
        name = "auto-" + _slug(task)
        p = os.path.join(os.path.dirname(__file__), "..", "recipes", name + ".md")
        with open(os.path.abspath(p), "w", encoding="utf-8") as f:
            f.write(f"# name: {name}\n# steps:\n" + "".join(f"- {s[:150]}\n" for s in steps))
        append_memory(f"Naya skill '{name}': {task[:80]}")
        return name
    except Exception:
        return ""
