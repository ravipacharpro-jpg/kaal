"""Real LLM calls — OpenAI-compatible /chat/completions, urllib only (no extra deps).
Key nahi to fail fast, router next endpoint try karta hai. Summary truncate.
Streaming: chat_stream token chunks on_chunk(txt) ko deta hai (TUI live).
"""
import json, urllib.request

TIMEOUT = 25

def chat(endpoint_url, api_key, model, messages, timeout=TIMEOUT, usage_cb=None,
         temperature=0.7, max_tokens=500):
    """Returns (ok, text). Real usage.total_tokens usage_cb ko (fake counting khatm)."""
    if not api_key:
        return False, "no-key"
    url = endpoint_url.rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model, "messages": messages[:10],
                       "max_tokens": max_tokens, "temperature": temperature}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        txt = d["choices"][0]["message"]["content"].strip()[:800]
        _usage(d, usage_cb)
        return True, txt
    except Exception as e:
        return False, _classify_err(e)

def _usage(d, cb):
    try:
        u = (d.get("usage") or {}).get("total_tokens", 0)
        if u and cb:
            cb(int(u))
    except Exception:
        pass

def chat_vision(endpoint_url, api_key, model, prompt, b64, mime="image/png",
                timeout=60, usage_cb=None):
    """Image + prompt. Vision-supporting model chahiye. Returns (ok, text)."""
    import base64
    if not api_key:
        return False, "no-key"
    url = endpoint_url.rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model, "max_tokens": 500, "messages": [{
        "role": "user", "content": [
            {"type": "text", "text": prompt[:500]},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        txt = d["choices"][0]["message"]["content"].strip()[:1000]
        _usage(d, usage_cb)
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

def chat_stream(endpoint_url, api_key, model, messages, on_chunk=None, timeout=60,
                usage_cb=None, temperature=0.7, max_tokens=500):
    """SSE streaming. on_chunk(piece) per token. Real usage via stream_options.
    Returns (ok, full_text_or_err)."""
    if not api_key:
        return False, "no-key"
    url = endpoint_url.rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model, "messages": messages[:10],
                       "max_tokens": max_tokens, "temperature": temperature,
                       "stream": True,
                       "stream_options": {"include_usage": True}}).encode()
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
                    if d.get("usage"):
                        _usage(d, usage_cb)
                    piece = d["choices"][0].get("delta", {}).get("content", "") if d.get("choices") else ""
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
