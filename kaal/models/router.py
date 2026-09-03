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

PROVIDER_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "mistral": "https://api.mistral.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "xai": "https://api.x.ai/v1",
}
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini", "openrouter": "auto",
    "groq": "llama-3.1-8b-instant", "together": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "mistral": "mistral-small-latest", "gemini": "gemini-2.0-flash",
    "xai": "grok-beta", "anthropic": "claude-3-5-haiku-latest",
}

MODEL_FILE = os.path.join(CONFIG_DIR, "model.json")

POPULAR_MODELS = [
    "auto", "anthropic/claude-sonnet-4", "anthropic/claude-3-5-haiku",
    "openai/gpt-4o", "openai/gpt-4o-mini", "google/gemini-2.0-flash",
    "meta-llama/llama-3.3-70b-instruct", "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat", "mistralai/mistral-small",
    "x-ai/grok-beta", "cohere/command-r-plus",
]

def get_model():
    d = _load_json(MODEL_FILE, {})
    return d.get("default_model", "auto")

def get_role_model(role):
    """architect/editor split (Aider style). Set nahi to default model."""
    d = _load_json(MODEL_FILE, {})
    return d.get(f"{role}_model", d.get("default_model", "auto"))

def set_role_model(role, name):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    d = _load_json(MODEL_FILE, {})
    d[f"{role}_model"] = name
    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    return f"{role} model set: {name}"

def set_model(name):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump({"default_model": name}, f, indent=2)
    return f"Model set: {name}"

def _model_for(prov):
    m = get_model()
    return m if m != "auto" else DEFAULT_MODELS.get(prov, "auto")

def try_chat(messages, max_tokens_note=200, model=None):
    """Multi-turn chat vault keys pe. model override (architect/editor) —
    openrouter pe jaisa-bola model, direct providers pe default. Key nahi to (rule-based, '')."""
    from .llm import chat
    vault = _load_json(VAULT, {"providers": {}})
    for prov, keys in vault.get("providers", {}).items():
        url = PROVIDER_URLS.get(prov)
        if not url or not isinstance(keys, list):
            continue
        m = model if (model and model != "auto" and prov == "openrouter") else _model_for(prov)
        if model and model != "auto" and prov != "openrouter" and "/" in model:
            m = model  # user jaanta hai — bhej do, fail to next provider
        for k in keys:
            key = k.get("key") if isinstance(k, dict) else k
            if not key:
                continue
            ok, txt = chat(url, key, m,
                           messages)
            if ok:
                track_usage(f"{prov}/key", max_tokens_note)
                return f"{prov}", txt
    return "rule-based", ""

def has_keys():
    vault = _load_json(VAULT, {"providers": {}})
    for keys in vault.get("providers", {}).values():
        if isinstance(keys, list) and any((k.get("key") if isinstance(k, dict) else k) for k in keys):
            return True
    return False

def try_llm(prompt, max_tokens_note=100):
    """User vault keys pe real LLM call, fallback chain. Returns (name, text).
    Key nahi to (rule-based, '') — agent local skills se kaam karta hai."""
    from .llm import chat
    vault = _load_json(VAULT, {"providers": {}})
    for prov, keys in vault.get("providers", {}).items():
        url = PROVIDER_URLS.get(prov)
        if not url or not isinstance(keys, list):
            continue
        for k in keys:
            key = k.get("key") if isinstance(k, dict) else k
            if not key:
                continue
            ok, txt = chat(url, key, _model_for(prov),
                           [{"role": "user", "content": prompt[:1500]}])
            if ok:
                track_usage(f"{prov}/key", max_tokens_note)
                return f"{prov}", txt
    return "rule-based", ""

def add_user_key(provider, key):
    """User ki unlimited API add karo — same provider ki multiple allowed."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    vault = _load_json(VAULT, {"providers": {}})
    vault.setdefault("providers", {}).setdefault(provider, []).append({"key": key})
    with open(VAULT, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2)
    return f"{provider} key add ho gayi ({len(vault['providers'][provider])} total)"
