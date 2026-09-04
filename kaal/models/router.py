"""Model router — OmniRoute/auto default + free-tier endpoints + multi-API per provider.
Agent khud select karta hai, user ko endpoint add nahi karna.
No code dump yahan — sirf selection summary return hota hai.
"""
import os, json, datetime

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

def _load_vault():
    """Vault padho: ENC1-encrypted (cryptography ho to) ya legacy plaintext JSON.
    Lib nahi to encrypted vault unreadable — {} (user ko notice milta hai)."""
    try:
        with open(VAULT, encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return {"providers": {}}
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    try:
        from .. import vault_crypto as _vc
        d = _vc.decrypt_payload(raw.strip())
        if isinstance(d, dict) and d:
            return d
    except Exception:
        pass
    return {"providers": {}}

def list_endpoints():
    """Sab endpoints + user vault keys merge karke do. Summary only."""
    user = _load_vault()
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
    _SESSION["tokens"] += tokens
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

def saver_active():
    """80%+ budget used? Saver: sequential tools, chhota context (SKILL 6)."""
    try:
        from .. import config_store as _cs
        daily, _ = _cs.get_budget()
        return budget_status(daily).get("pct", 0) >= 80
    except Exception:
        return False

PROVIDER_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "mistral": "https://api.mistral.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "xai": "https://api.x.ai/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "kimi": "https://api.moonshot.cn/v1",
    "glm": "https://open.bigmodel.cn/api/paas/v4",
    "tongyi": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini", "openrouter": "auto",
    "groq": "llama-3.1-8b-instant", "together": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "mistral": "mistral-small-latest", "gemini": "gemini-2.0-flash",
    "xai": "grok-beta", "anthropic": "claude-3-5-haiku-latest",
    "deepseek": "deepseek-chat", "kimi": "moonshot-v1-8k",
    "glm": "glm-4-plus", "tongyi": "qwen-max",
}

MODEL_FILE = os.path.join(CONFIG_DIR, "model.json")

POPULAR_MODELS = [
    "auto", "anthropic/claude-sonnet-4", "anthropic/claude-3-5-haiku",
    "openai/gpt-4o", "openai/gpt-4o-mini", "google/gemini-2.0-flash",
    "meta-llama/llama-3.3-70b-instruct", "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat", "mistralai/mistral-small",
    "x-ai/grok-beta", "cohere/command-r-plus",
    "deepseek/deepseek-chat", "moonshot-v1-8k", "glm-4-plus", "qwen-max",
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

EFFORTS = {"low": (0.2, 200), "medium": (0.7, 500), "high": (1.0, 1000)}

def get_effort():
    """Reasoning effort: low|medium|high. Default medium."""
    d = _load_json(MODEL_FILE, {})
    e = str(d.get("effort", "medium")).lower()
    return e if e in EFFORTS else "medium"

def set_effort(name):
    name = str(name or "").lower()
    if name not in EFFORTS:
        return f"Effort galat — use: {', '.join(EFFORTS)}"
    os.makedirs(CONFIG_DIR, exist_ok=True)
    d = _load_json(MODEL_FILE, {})
    d["effort"] = name
    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    t, n = EFFORTS[name]
    return f"Effort set: {name} (temperature {t}, max_tokens {n})"

def _effort_params():
    t, n = EFFORTS[get_effort()]
    return {"temperature": t, "max_tokens": n, "num_predict": n}

def _cache_store(prov, model, messages, txt, tokens):
    """Success pe cache me dalo (fail-soft)."""
    try:
        from ..skills import promptcache as _pc
        import json as _js
        last = str(messages[-1].get("content", ""))[:1500] if messages else ""
        _pc.store(last, txt, _js.dumps(messages[:-1])[:2000], model, tokens)
    except Exception:
        pass

def _model_for(prov):
    m = get_model()
    return m if m != "auto" else DEFAULT_MODELS.get(prov, "auto")

def try_chat(messages, max_tokens_note=200, model=None):
    """Pehle keyless Ollama local, phir vault keys.
    Rate-limit wali key 60s cooldown (smart rotation), auth-fail wali skip nahi (user fix karega).
    Returns (name, text). Dono nahi to (rule-based, '')."""
    from . import ollama as _ol
    got0 = []
    try:
        ep = _effort_params()
        ok, txt = _ol.chat(messages, usage_cb=lambda n: got0.append(n),
                           temperature=ep["temperature"], num_predict=ep["num_predict"])
        if ok:
            track_usage("ollama_local", got0[0] if got0 else max_tokens_note)
            return "ollama_local", txt
    except Exception:
        pass
    from .llm import chat
    import time as _t
    vault = _load_vault()
    for prov, keys in vault.get("providers", {}).items():
        url = PROVIDER_URLS.get(prov)
        if not url or not isinstance(keys, list):
            continue
        m = model if (model and model != "auto" and prov == "openrouter") else _model_for(prov)
        if model and model != "auto" and prov != "openrouter" and "/" in model:
            m = model  # user jaanta hai — bhej do, fail to next provider
        try:
            from ..skills import promptcache as _pc
            import json as _js
            _plast = str(messages[-1].get("content", ""))[:1500]
            _hit, _cached = _pc.lookup(_plast, _js.dumps(messages[:-1])[:2000], m)
            if _hit:
                return f"{prov} (cache)", _cached
        except Exception:
            pass
        for k in keys:
            ent = _entry(k)
            key = ent.get("key") or ""
            if not key or ent.get("status") == "dead":
                continue  # dead keys rotation se bahar
            if _cool(str(key)) > _t.time():
                continue  # rate-limit cooldown me hai — next key
            got1 = []
            ep1 = _effort_params()
            ok, txt = chat(url, key, m, messages, usage_cb=lambda n: got1.append(n),
                           temperature=ep1["temperature"], max_tokens=ep1["max_tokens"])
            note_key_result(prov, key, ok, txt)
            if ok:
                track_usage(f"{prov}/key", got1[0] if got1 else max_tokens_note)
                _cache_store(prov, m, messages, txt, got1[0] if got1 else 0)
                return f"{prov}", txt
    return "rule-based", ""

def try_chat_stream(messages, model=None, on_token=None, max_tokens_note=200):
    """Streaming chat: Ollama local pehle, phir vault keys (SSE).
    on_token(piece) per chunk. Returns (name, full_text)."""
    from . import ollama as _ol
    got = []
    try:
        ep = _effort_params()
        ok, txt = _ol.chat_stream(messages, on_token=on_token,
                                   usage_cb=lambda n: got.append(n),
                                   temperature=ep["temperature"],
                                   num_predict=ep["num_predict"])
        if ok:
            track_usage("ollama_local", got[0] if got else max_tokens_note)
            return "ollama_local", txt
    except Exception:
        pass
    from .llm import chat_stream
    import time as _t
    vault = _load_vault()
    for prov, keys in vault.get("providers", {}).items():
        url = PROVIDER_URLS.get(prov)
        if not url or not isinstance(keys, list):
            continue
        m = model if (model and model != "auto" and prov == "openrouter") else _model_for(prov)
        if model and model != "auto" and prov != "openrouter" and "/" in model:
            m = model
        for k in keys:
            ent = _entry(k)
            key = ent.get("key") or ""
            if not key or ent.get("status") == "dead":
                continue
            if _cool(str(key)) > _t.time():
                continue
            got2 = []
            ep2 = _effort_params()
            ok, txt = chat_stream(url, key, m, messages, on_token=on_token,
                                  usage_cb=lambda n: got2.append(n),
                                  temperature=ep2["temperature"],
                                  max_tokens=ep2["max_tokens"])
            note_key_result(prov, key, ok, txt)
            if ok:
                track_usage(f"{prov}/key", got2[0] if got2 else max_tokens_note)
                return f"{prov}", txt
    return "rule-based", ""

_COOL = {}

_NOTICES = []
DEAD_AFTER_FAILS = 3

def pop_notices():
    """TUI notifications (dead-key alerts) lao + clear karo."""
    out = list(_NOTICES)
    del _NOTICES[:]
    return out

def _entry(k):
    """Key entry normalize karo (legacy string/plain-dict safe).
    Shape: {key, fail_count, last_fail, status}."""
    if isinstance(k, dict):
        d = dict(k)
    else:
        d = {"key": k}
    d.setdefault("fail_count", 0)
    d.setdefault("last_fail", None)
    d.setdefault("status", "active")
    try:
        d["fail_count"] = int(d.get("fail_count") or 0)
    except Exception:
        d["fail_count"] = 0
    if d.get("status") not in ("active", "cooldown", "dead"):
        d["status"] = "active"
    return d

def _save_vault_map(vault):
    """Vault map persist karo (encrypt-aware) + 0600. Returns mode str."""
    mode = "plaintext+0600"
    try:
        from .. import vault_crypto as _vc
        ok, payload = _vc.encrypt_dict(vault)
        if ok:
            with open(VAULT, "w", encoding="utf-8") as f:
                f.write(payload)
            mode = "encrypted"
        else:
            raise RuntimeError("no-crypto")
    except Exception:
        with open(VAULT, "w", encoding="utf-8") as f:
            json.dump(vault, f, indent=2)
    try:
        os.chmod(VAULT, 0o600)
    except OSError:
        pass
    return mode

def _find_entry(vault, provider, key):
    for i, k in enumerate(vault.get("providers", {}).get(provider, []) or []):
        e = _entry(k)
        if e.get("key") == key:
            return i, e
    return None, None

def note_key_result(provider, key, ok, err=""):
    """Rotation health update. rate-limit → 60s cooldown (count nahi).
    auth-fail/quota-exceeded → fail_count++ (consecutive); 3 pe dead + notice.
    success → count reset. Vault persist hota hai."""
    import time as _t
    try:
        vault = _load_vault()
        idx, ent = _find_entry(vault, provider, key)
        if ent is None:
            return
        err = str(err or "")
        if ok:
            ent["fail_count"] = 0
            ent["last_fail"] = None
            if ent["status"] == "cooldown":
                ent["status"] = "active"
        elif err.startswith("rate-limit:"):
            _cool(str(key), 60)
            ent["status"] = "cooldown"
        elif err.startswith("auth-fail:") or err.startswith("quota-exceeded:"):
            ent["fail_count"] = ent.get("fail_count", 0) + 1
            ent["last_fail"] = _t.time()
            if ent["fail_count"] >= DEAD_AFTER_FAILS and ent["status"] != "dead":
                ent["status"] = "dead"
                n = idx + 1
                _NOTICES.append(
                    f" {provider} key #{n} dead ho gayi "
                    f"({'quota' if err.startswith('quota') else 'auth-fail'}, "
                    f"{ent['fail_count']}x fail) — rotation se bahar. "
                    f"/keys revive {provider} {n} se wapas lao.")
        vault["providers"][provider][idx] = ent
        os.makedirs(CONFIG_DIR, exist_ok=True)
        _save_vault_map(vault)
    except Exception:
        pass

def revive_key(provider, n):
    """Dead/cooldown key wapas active karo (1-based index)."""
    try:
        vault = _load_vault()
        lst = vault.get("providers", {}).get(provider, []) or []
        i = int(n) - 1
        if i < 0 or i >= len(lst):
            return f"Key #{n} nahi mili ({provider}: {len(lst)} keys)"
        ent = _entry(lst[i])
        ent["fail_count"] = 0
        ent["last_fail"] = None
        ent["status"] = "active"
        vault["providers"][provider][i] = ent
        os.makedirs(CONFIG_DIR, exist_ok=True)
        _save_vault_map(vault)
        return f"{provider} key #{n} revive ho gayi (active)"
    except Exception as e:
        return f"Revive fail: {e}"[:150]

def key_health(provider=""):
    """{provider: [{n, masked, status, fails}]} — /keys list ke liye."""
    vault = _load_vault()
    out = {}
    for prov, keys in (vault.get("providers") or {}).items():
        if provider and prov != provider:
            continue
        rows = []
        for i, k in enumerate(keys or [], 1):
            e = _entry(k)
            key = str(e.get("key") or "")
            rows.append({"n": i,
                         "masked": key[:6] + "..." + key[-4:] if len(key) > 12 else "***",
                         "status": e.get("status", "active"),
                         "fails": e.get("fail_count", 0)})
        out[prov] = rows
    return out

_SESSION = {"tokens": 0}

def session_used():
    """Is process me ab tak kitne tokens kharch hue."""
    return _SESSION["tokens"]

def session_reset():
    _SESSION["tokens"] = 0
    return "Session counter reset"

def session_cap():
    """Per-session token cap (economy.session_cap, default 2000)."""
    try:
        from .. import config_store as _cs
        return int(_cs.get_all().get("economy", {}).get("session_cap", 2000))
    except Exception:
        return 2000

def session_over():
    """Cap cross hua? True to brain band, legacy-only (budget burn guard)."""
    return session_used() >= session_cap()

def _cool(key, secs=0):
    """Cooldown registry. _cool(key) -> expiry ts; _cool(key, 60) sets."""
    import time as _t
    fp = f"{len(key)}:{key[:6]}:{key[-4:]}"
    if secs:
        _COOL[fp] = _t.time() + secs
        return _COOL[fp]
    return _COOL.get(fp, 0)

def has_keys():
    vault = _load_vault()
    for keys in vault.get("providers", {}).values():
        if isinstance(keys, list) and any((k.get("key") if isinstance(k, dict) else k) for k in keys):
            return True
    return False

def brain_active():
    """Brain tab jab vault key ho YA Ollama local chal raha ho (keyless AI)."""
    if has_keys():
        return True
    try:
        from . import ollama as _ol
        ok, _ = _ol.detect()
        return ok
    except Exception:
        return False

def try_llm(prompt, max_tokens_note=100):
    """User vault keys pe real LLM call, rate-limit cooldown rotation.
    Key nahi to (rule-based, '') — agent local skills se kaam karta hai."""
    from .llm import chat
    import time as _t
    vault = _load_vault()
    for prov, keys in vault.get("providers", {}).items():
        url = PROVIDER_URLS.get(prov)
        if not url or not isinstance(keys, list):
            continue
        try:
            from ..skills import promptcache as _pc2
            _hit2, _cached2 = _pc2.lookup(prompt[:1500], "", _model_for(prov))
            if _hit2:
                return f"{prov} (cache)", _cached2
        except Exception:
            pass
        for k in keys:
            ent = _entry(k)
            key = ent.get("key") or ""
            if not key or ent.get("status") == "dead":
                continue
            if _cool(str(key)) > _t.time():
                continue
            got3 = []
            ep3 = _effort_params()
            ok, txt = chat(url, key, _model_for(prov),
                           [{"role": "user", "content": prompt[:1500]}],
                           usage_cb=lambda n: got3.append(n),
                           temperature=ep3["temperature"], max_tokens=ep3["max_tokens"])
            note_key_result(prov, key, ok, txt)
            if ok:
                track_usage(f"{prov}/key", got3[0] if got3 else max_tokens_note)
                _cache_store(prov, _model_for(prov),
                             [{"role": "user", "content": prompt[:1500]}],
                             txt, got3[0] if got3 else 0)
                return f"{prov}", txt
    return "rule-based", ""

def try_vision(prompt, b64, mime="image/png"):
    """Image describe via vault keys (vision models). Returns (name, text)."""
    from .llm import chat_vision
    import time as _t
    vault = _load_vault()
    for prov, keys in vault.get("providers", {}).items():
        url = PROVIDER_URLS.get(prov)
        if not url or not isinstance(keys, list):
            continue
        for k in keys:
            ent = _entry(k)
            key = ent.get("key") or ""
            if not key or ent.get("status") == "dead":
                continue
            if _cool(str(key)) > _t.time():
                continue
            got = []
            ok, txt = chat_vision(url, key, _model_for(prov), prompt, b64, mime,
                                  usage_cb=lambda n: got.append(n))
            note_key_result(prov, key, ok, txt)
            if ok:
                track_usage(f"{prov}/key", got[0] if got else 300)
                return f"{prov}", txt
    return "rule-based", ""

def estimate(task, steps=3):
    """Pre-run cost estimate (~tokens). Rule-of-thumb, guarantee nahi."""
    toks = int(len(task) * 1.3 + steps * 150 + 300)
    daily, _ = 5000, 0
    try:
        from .. import config_store as _cfg
        daily, _ = _cfg.get_budget()
        used = budget_status(daily)["used"]
    except Exception:
        used = 0
    left = max(0, daily - used)
    flag = "  budget me" if toks <= left else "  budget se zyada lag sakta"
    return f"≈{toks} tokens{flag}"

def add_user_key(provider, key):
    """User ki unlimited API add karo — same provider ki multiple allowed.
    Entry shape: {key, fail_count, last_fail, status}. cryptography mili to
    AES-encrypted vault, nahi to plaintext + 0600."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    vault = _load_vault()
    vault.setdefault("providers", {}).setdefault(provider, []).append(
        {"key": key, "fail_count": 0, "last_fail": None, "status": "active"})
    mode = _save_vault_map(vault)
    n = len(vault['providers'][provider])
    return f"{provider} key add ho gayi ({n} total, {mode})"

def vault_summary():
    """Vault ka masked summary: {provider: ['sk-ab12...wxyz', ...]}. Keys kabhi poori nahi."""
    out = {}
    for prov, rows in key_health().items():
        out[prov] = [r["masked"] for r in rows]
    return out

def get_github_token():
    """Vault se pehli active github key lao (token LLM ko kabhi nahi dikhta).
    Nahi mili to '' (unauthenticated, rate-limit kam)."""
    try:
        vault = _load_vault()
        for k in (vault.get("providers") or {}).get("github", []) or []:
            e = _entry(k)
            if e.get("status") != "dead" and e.get("key"):
                return str(e["key"])
    except Exception:
        pass
    return ""
