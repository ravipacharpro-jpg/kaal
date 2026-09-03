"""Ollama local auto-detect — running hai to unlimited local endpoint active."""
import json, urllib.request

URLS = ["http://localhost:11434", "http://127.0.0.1:11434"]

def detect(timeout=3):
    """Returns (running, models[]). Koi server nahi to (False, [])."""
    for base in URLS:
        try:
            with urllib.request.urlopen(base + "/api/tags", timeout=timeout) as r:
                d = json.load(r)
            models = [m.get("name", "?") for m in d.get("models", [])][:10]
            return True, models
        except Exception:
            continue
    return False, []

def status_line():
    ok, models = detect()
    if not ok:
        return "Ollama: nahi chal raha (optional — chalao to free local)"
    ms = ", ".join(models) if models else "koi model load nahi"
    return f"Ollama: chal raha ✅ models: {ms}"

def chat(messages, timeout=60):
    """Keyless local LLM call. Returns (ok, text). Ollama band to (False, reason)."""
    ok, text, _ = chat_stream(messages, timeout=timeout)
    return ok, text

def chat_stream(messages, on_token=None, timeout=120):
    """Streaming chat. on_token(piece) per chunk. Returns (ok, full_or_err)."""
    ok, models = detect()
    if not ok:
        return False, "ollama-off"
    model = models[0] if models else "llama3.2"
    body = json.dumps({"model": model, "messages": messages,
                       "stream": True,
                       "options": {"num_predict": 500}}).encode()
    for base in URLS:
        try:
            req = urllib.request.Request(base + "/api/chat", data=body,
                                         headers={"Content-Type": "application/json"})
            full = []
            with urllib.request.urlopen(req, timeout=timeout) as r:
                for line in r:
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    piece = (d.get("message", {}) or {}).get("content", "")
                    if piece:
                        full.append(piece)
                        if on_token:
                            try:
                                on_token(piece)
                            except Exception:
                                pass
                    if d.get("done"):
                        break
            txt = "".join(full).strip()[:2000]
            if txt:
                return True, txt
        except Exception:
            continue
    return False, "ollama-fail"

# Hermes-style uncensored + popular local presets (ollama pull <name>)
PRESETS = [
    "nous-hermes2", "llama3.2:1b", "llama3.2:3b", "phi3:mini",
    "qwen2.5:3b", "mistral:7b", "codellama:7b", "gemma2:2b",
]

def pull(model, timeout=600):
    """ollama pull <model>. Lamba chal sakta hai — summary return."""
    for base in URLS:
        try:
            body = json.dumps({"name": model}).encode()
            req = urllib.request.Request(base + "/api/pull", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                last = ""
                for line in r:
                    try:
                        d = json.loads(line)
                        last = d.get("status", "")
                        if d.get("status") == "success":
                            return f"Pull ho gaya: {model} ✅"
                    except Exception:
                        pass
                return f"Pull: {model} — {last[:100] or 'adhura'}"
        except Exception as e:
            continue
    return "Ollama nahi chal raha — pehle `ollama serve` karo"
