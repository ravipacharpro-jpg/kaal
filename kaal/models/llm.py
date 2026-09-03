"""Real LLM calls — OpenAI-compatible /chat/completions, urllib only (no extra deps).
Key nahi to fail fast, router next endpoint try karta hai. Summary truncate.
Streaming: chat_stream token chunks on_chunk(txt) ko deta hai (TUI live).
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
        return False, _classify_err(e)

def _classify_err(e):
    s = str(e)[:150]
    low = s.lower()
    if "429" in s or "rate" in low and "limit" in low or "too many" in low:
        return "rate-limit: " + s
    if "401" in s or "unauthorized" in low or "invalid" in low and "key" in low:
        return "auth-fail: " + s
    return s

def chat_stream(endpoint_url, api_key, model, messages, on_chunk=None, timeout=60):
    """SSE streaming. on_chunk(piece) per token. Returns (ok, full_text_or_err)."""
    if not api_key:
        return False, "no-key"
    url = endpoint_url.rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model, "messages": messages[:10],
                       "max_tokens": 500, "temperature": 0.7,
                       "stream": True}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    full = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for line in r:
                s = line.decode("utf-8", "replace").strip()
                if not s.startswith("data:"):
                    continue
                data = s[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    d = json.loads(data)
                    piece = d["choices"][0].get("delta", {}).get("content", "")
                except Exception:
                    continue
                if piece:
                    full.append(piece)
                    if on_chunk:
                        try:
                            on_chunk(piece)
                        except Exception:
                            pass
        return True, "".join(full).strip()[:2000]
    except Exception as e:
        return False, _classify_err(e)
