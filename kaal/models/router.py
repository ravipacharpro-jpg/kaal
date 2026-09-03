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
    {"name": "together_free", "url": "https://api.together.xyz/v1",
     "key": "", "daily_limit": 5000, "free": True,
     "desc": "Together AI community tier"},
    {"name": "fireworks_free", "url": "https://api.fireworks.ai/inference/v1",
     "key": "", "daily_limit": 5000, "free": True,
     "desc": "Fireworks AI community tier"},
    {"name": "deepinfra_free", "url": "https://api.deepinfra.com/v1/openai",
     "key": "", "daily_limit": 2000, "free": True,
     "desc": "DeepInfra community tier"},
    {"name": "anyscale_free", "url": "https://api.endpoints.anyscale.com/v1",
     "key": "", "daily_limit": 2000, "free": True,
     "desc": "Anyscale community tier"},
    {"name": "perplexity_free", "url": "https://api.perplexity.ai",
     "key": "", "daily_limit": 1000, "free": True,
     "desc": "Perplexity search AI community"},
    {"name": "cohere_free", "url": "https://api.cohere.ai/compatibility/v1",
     "key": "", "daily_limit": 1000, "free": True,
     "desc": "Cohere compatibility tier"},
    {"name": "mistral_free", "url": "https://api.mistral.ai/v1",
     "key": "", "daily_limit": 1000, "free": True,
     "desc": "Mistral La Plateforme free"},
    {"name": "gemini_free", "url": "https://generativelanguage.googleapis.com/v1beta/openai",
     "key": "", "daily_limit": 1500, "free": True,
     "desc": "Google AI Studio free tier"},
    {"name": "openai_free", "url": "https://api.openai.com/v1",
     "key": "", "daily_limit": 500, "free": True,
     "desc": "OpenAI tier (key se, free credit)"},
    {"name": "anthropic_free", "url": "https://api.anthropic.com/v1",
     "key": "", "daily_limit": 500, "free": True,
     "desc": "Anthropic tier (key se, free credit)"},
    {"name": "xai_free", "url": "https://api.x.ai/v1",
     "key": "", "daily_limit": 500, "free": True,
     "desc": "xAI community tier"},
    {"name": "replicate_free", "url": "https://api.replicate.com/v1",
     "key": "", "daily_limit": 500, "free": True,
     "desc": "Replicate community credit"},
    {"name": "octoai_free", "url": "https://text.octoai.run/v1",
     "key": "", "daily_limit": 2000, "free": True,
     "desc": "OctoAI community tier"},
    {"name": "nebius_free", "url": "https://api.studio.nebius.com/v1",
     "key": "", "daily_limit": 2000, "free": True,
     "desc": "Nebius AI Studio free"},
    {"name": "hyperbolic_free", "url": "https://api.hyperbolic.xyz/v1",
     "key": "", "daily_limit": 2000, "free": True,
     "desc": "Hyperbolic community tier"},
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

def track_usage(name, tokens=100):
    """Endpoint usage badhao, daily reset ke saath. Returns (used, limit)."""
    import datetime as _dt
    usage = _load_json(USAGE, {})
    today = _dt.date.today().isoformat()
    if usage.get("date") != today:
        usage = {"date": today}
    usage[name] = usage.get(name, 0) + tokens
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(USAGE, "w", encoding="utf-8") as f:
            json.dump(usage, f, indent=2)
    except Exception:
        pass
    lim = next((e["daily_limit"] for e in BUILTIN_FREE if e["name"] == name), -1)
    return usage[name], lim

def budget_status(daily_budget=5000):
    """Total free-tier usage summary. TUI /budget ke liye."""
    import datetime as _dt
    usage = _load_json(USAGE, {})
    today = _dt.date.today().isoformat()
    if usage.get("date") != today:
        return {"used": 0, "budget": daily_budget, "pct": 0, "mode": "auto/smart"}
    used = sum(v for k, v in usage.items() if k != "date")
    pct = min(100, int(used * 100 / daily_budget)) if daily_budget else 0
    mode = "auto/fast (budget saver)" if pct >= 80 else "auto/smart"
    return {"used": used, "budget": daily_budget, "pct": pct, "mode": mode}

def add_user_key(provider, key):
    """User ki unlimited API add karo — same provider ki multiple allowed."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    vault = _load_json(VAULT, {"providers": {}})
    vault.setdefault("providers", {}).setdefault(provider, []).append({"key": key})
    with open(VAULT, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2)
    return f"{provider} key add ho gayi ({len(vault['providers'][provider])} total)"
