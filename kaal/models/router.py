"""Model router — OmniRoute/auto default + free-tier endpoints + multi-API per provider.
Agent khud select karta hai, user ko endpoint add nahi karna.
No code dump yahan — sirf selection summary return hota hai.
"""
import os, json, datetime

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "config")
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config"))
VAULT = os.path.join(CONFIG_DIR, "vault.json")
USAGE = os.path.join(CONFIG_DIR, "endpoint_usage.json")

BUILTIN_FREE = [
    {"name": "omniroute/auto", "url": "https://openrouter.ai/api/v1",
     "key": "omniroute_auto", "daily_limit": -1, "free": True,
     "desc": "Built-in 90+ free tiers, keyless"},
    {"name": "openrouter_free", "url": "https://openrouter.ai/api/v1",
     "key": "community_tier", "daily_limit": 1000, "free": True,
     "desc": "OpenRouter free tier routing"},
    {"name": "groq_free", "url": "https://api.groq.com/openai/v1",
     "key": "", "daily_limit": 30000, "free": True,
     "desc": "Groq fast inference community"},
    {"name": "hf_free", "url": "https://api-inference.huggingface.co/models",
     "key": "", "daily_limit": 1000, "free": True,
     "desc": "HuggingFace inference free"},
    {"name": "ollama_local", "url": "http://localhost:11434/v1",
     "key": "local", "daily_limit": -1, "free": True,
     "desc": "Device-local Ollama, unlimited if running"},
]

def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def list_endpoints():
    """Sab endpoints + user vault keys merge karke do. Summary only."""
    user = _load_json(VAULT, {"providers": {}})
    eps = [dict(e) for e in BUILTIN_FREE]
    for prov, keys in user.get("providers", {}).items():
        if isinstance(keys, list):
            for i, k in enumerate(keys):
                key = k.get("key") if isinstance(k, dict) else k
                if not key:
                    continue
                eps.append({"name": f"{prov}/key{i+1}", "url": f"user:{prov}",
                            "key": "***", "daily_limit": -1, "free": False,
                            "desc": f"User {prov} key {i+1}"})
    return eps

def select_endpoint(task_budget=500):
    """Best free endpoint select karo. Pehla available = omniroute/auto."""
    usage = _load_json(USAGE, {})
    today = datetime.date.today().isoformat()
    if usage.get("date") != today:
        usage = {"date": today}
    for e in list_endpoints():
        used = usage.get(e["name"], 0)
        lim = e["daily_limit"]
        if lim == -1 or used < lim:
            return e
    return {"name": "rule-based", "url": "local", "key": "",
            "daily_limit": -1, "free": True, "desc": "Emergency fallback"}

def add_user_key(provider, key):
    """User ki unlimited API add karo — same provider ki multiple allowed."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    vault = _load_json(VAULT, {"providers": {}})
    vault.setdefault("providers", {}).setdefault(provider, []).append({"key": key})
    with open(VAULT, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2)
    return f"{provider} key add ho gayi ({len(vault['providers'][provider])} total)"
