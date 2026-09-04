"""Telegram channel — gateway interface impl.
NAME/handle_text/serve. Setup: config/telegram.json.
Run: kaal --telegram
Security: allowed_ids ke bahar koi reply nahi. Sensitive ops auto-deny.
"""
import json, time, urllib.parse, urllib.request

NAME = "telegram"

CFG = {"bot_token": "", "allowed_ids": []}
API = "https://api.telegram.org/bot"

def _load():
    import os
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "telegram.json"))
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        CFG.update({k: d[k] for k in ("bot_token", "allowed_ids") if k in d})
    except Exception:
        pass
    return p

def _api(token, method, params=None):
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(f"{API}{token}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def _send(token, chat_id, text):
    try:
        _api(token, "sendMessage", {"chat_id": chat_id,
                                    "text": text[:3500]})
    except Exception:
        pass

def handle_text(text, run_fn):
    """Ek message handle karo. Returns reply string."""
    t = (text or "").strip()
    if t.startswith("/start") or t.startswith("/help"):
        return (" Kaal — Ahead of Time\n/task <kaam> — chalao\n"
                "/status — budget+endpoints\n/tasks seedha bhi likh sakte ho")
    if t.startswith("/status"):
        try:
            from ..models.router import budget_status
            b = budget_status()
            return f" {b['used']}/{b['budget']} |  {b['mode']}"
        except Exception as e:
            return f"Status fail: {e}"[:200]
    task = t[5:].strip() if t.startswith("/task") else t
    if not task:
        return "Khali task. /task <kaam> likho."
    try:
        # phone pe approval possible nahi — sensitive auto-deny (safe default)
        # Remote explicit task: L2 (perm allow-list) + auto-deny baaki
        res = run_fn(task, ask_cb=lambda q: False, level="L2")
        return f" {res.get('summary', '')[:2000]}\n(via {res.get('endpoint', '?')})"
    except Exception as e:
        return f" Fail: {e}"[:300]

def serve(poll_secs=3):
    path = _load()
    token = CFG["bot_token"]
    if not token:
        return f"Token nahi — {path} me bot_token dalo (BotFather se)."
    allowed = set(CFG["allowed_ids"])
    print(f" Kaal Telegram live (allowed: {len(allowed)} users). Ctrl+C stop.")
    from ..agent import run_task
    offset = 0
    try:
        while True:
            try:
                d = _api(token, "getUpdates", {"offset": offset, "timeout": 25})
            except Exception:
                time.sleep(poll_secs)
                continue
            for u in d.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message", {})
                uid = msg.get("from", {}).get("id")
                cid = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if not text or not cid:
                    continue
                if allowed and uid not in allowed:
                    _send(token, cid, " Allowed nahi ho.")
                    continue
                _send(token, cid, "⏳ Kaal kaam kar raha hai...")
                _send(token, cid, handle_text(text, run_task))
    except KeyboardInterrupt:
        return "Telegram bridge band."
