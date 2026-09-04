"""Config store — defaults + config/*.json merge. Economy, permissions, TUI sab yahan.
User file nahi to defaults. Agent khud padhta hai, user ko haath se edit nahi karna.
"""
import os, json
from .config_defaults import DEFAULTS

REPO_CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
FILES = {"economy": "economy.json", "permissions": "permissions.json", "tui": "tui.json",
         "storage": "storage.json", "sandbox": "sandbox.json", "model": "model.json"}

def _load(name):
    try:
        with open(os.path.join(REPO_CONFIG, FILES[name]), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def _save(name, d):
    os.makedirs(REPO_CONFIG, exist_ok=True)
    with open(os.path.join(REPO_CONFIG, FILES[name]), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)

def _merge(base, over):
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out

def get_all():
    cfg = json.loads(json.dumps(DEFAULTS))
    for n in ("economy", "permissions", "tui", "storage", "sandbox", "model"):
        cfg = _merge(cfg, _load(n))
    # flat keys support: economy.json me {"daily_budget":..} seedha
    eco = _load("economy")
    if "daily_budget" in eco: cfg["economy"]["daily_budget"] = eco["daily_budget"]
    if "per_task_budget" in eco: cfg["economy"]["per_task_budget"] = eco["per_task_budget"]
    if "policy" in eco: cfg["economy"]["policy"] = eco["policy"]
    per = _load("permissions")
    for k, v in per.items():
        if isinstance(v, str): cfg["permissions"][k] = v
    return cfg

def get_budget():
    c = get_all()["economy"]
    return int(c.get("daily_budget", 5000)), int(c.get("per_task_budget", 500))

def get_perm(op):
    return get_all()["permissions"].get(op, "ask")

def set_perm(op, val):
    d = _load("permissions")
    d[op] = val
    _save("permissions", d)
    return f"{op} = {val}"

def check_perm(op, ask_cb=None, prompt=""):
    """allow→True, deny→False, ask→prompt (default deny on no-callback)."""
    mode = get_perm(op)
    if mode == "allow":
        return True
    if mode == "deny":
        return False
    if ask_cb:
        return bool(ask_cb(prompt or f"{op} ki permission du?"))
    return False
