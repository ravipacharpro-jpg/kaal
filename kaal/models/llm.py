"""Real LLM calls — OpenAI-compatible /chat/completions, urllib only (no extra deps).
Key nahi to fail fast, router next endpoint try karta hai. Summary truncate.
"""
import json, urllib.request

TIMEOUT = 25

def chat(endpoint_url, api_key, model, messages, timeout=TIMEOUT):
    """Returns (ok, text). ok=False pe router fallback karega."""
    if not api_key:
        return False, "no-key"
    url = endpoint_url.rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model, "messages": messages[:10],
                       "max_tokens": 500, "temperature": 0.7}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        txt = d["choices"][0]["message"]["content"].strip()[:800]
        return True, txt
    except Exception as e:
        return False, str(e)[:150]
