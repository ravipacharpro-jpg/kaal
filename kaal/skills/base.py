"""Skill protocol — core extensible design.
Naya skill add karna = naya module + SKILL dict + (optional) hooks. Core chhuna nahi padta.

SKILL shape (dict):
{
  "name": "my-skill",        # unique id
  "desc": "1-line Hindi/English", 
  "version": "0.1.0",
  "tools": [ {name, desc, params, fn} ... ],   # brain TOOLS me merge (optional)
  "commands": ["/my-cmd ...", ...],            # palette/TUI me (optional, docs only)
  "on_task": fn(task) -> str,     # task start pe context note (optional)
  "on_result": fn(task, summary), # task end pe (reflection jaisa, optional)
}
Rules: hooks kabhi crash nahi karenge (registry fail-soft). Code/identifiers
English-only; comments kisi bhi language me.
"""
import importlib

REGISTRY = {}

BUILTINS = ["files", "code", "repl", "browser", "project", "dev", "semsearch",
            "promptcache", "zhcomment", "reflect", "lsp", "secrets", "shell",
            "git", "vision", "sandbox", "rules", "pluginman"]

def register(skill):
    """SKILL dict register karo. Returns name. Galat shape to ValueError."""
    if not isinstance(skill, dict) or not skill.get("name"):
        raise ValueError("SKILL me 'name' chahiye")
    REGISTRY[str(skill["name"])] = skill
    return str(skill["name"])

def _load_builtin(mod):
    try:
        m = importlib.import_module(f"{__package__}.{mod}")
        sk = getattr(m, "SKILL", None)
        if isinstance(sk, dict) and sk.get("name"):
            REGISTRY.setdefault(str(sk["name"]), sk)
            return True
    except Exception:
        pass
    return False

def autodiscover():
    """Saare built-in SKILL dicts load karo (idempotent)."""
    for mod in BUILTINS:
        _load_builtin(mod)
    return sorted(REGISTRY)

def all_skills():
    autodiscover()
    return dict(REGISTRY)

def skill_tools():
    """Sab skills ke tools (brain merge ke liye)."""
    out = []
    for sk in all_skills().values():
        for t in (sk.get("tools") or []):
            if isinstance(t, dict) and t.get("name") and callable(t.get("fn")):
                out.append(t)
    return out

def hook(name, *args):
    """on_task/on_result hooks chalao. Returns [notes]. Fail-soft."""
    notes = []
    for sk in all_skills().values():
        fn = sk.get(name)
        if not callable(fn):
            continue
        try:
            r = fn(*args)
            if r:
                notes.append(str(r)[:300])
        except Exception:
            continue
    return notes
