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
