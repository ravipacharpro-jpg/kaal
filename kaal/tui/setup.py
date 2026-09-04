"""Setup/Keys tab — onboarding: provider keys masked input se vault me.
First-run pe auto (marker config/.onboarded), /setup se manual.
GitHub token bhi isi vault me (LLM ko kabhi nahi dikhta — tools vault se lete hain).
"""
import os

PROVIDERS = ["openai", "anthropic", "groq", "together", "mistral", "gemini",
             "xai", "openrouter", "deepseek", "kimi", "glm", "tongyi", "github"]

def _marker():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "config", ".onboarded"))

def needs_onboarding():
    """Vault khaali + marker nahi = first run."""
    try:
        from ..models.router import key_health
        has = any(rows for rows in key_health().values())
        return (not has) and (not os.path.isfile(_marker()))
    except Exception:
        return False

def mark_done():
    try:
        os.makedirs(os.path.dirname(_marker()), exist_ok=True)
        with open(_marker(), "w", encoding="utf-8") as f:
            f.write("onboarded\n")
    except Exception:
        pass

def ping_key(provider, key, timeout=8):
    """Chhota ping: key valid? Returns (ok, msg). Network nahi to (False, reason)."""
    import json
    import urllib.request
    key = (key or "").strip()
    if not key:
        return False, "key khaali"
    try:
        if provider == "github":
            req = urllib.request.Request("https://api.github.com/user",
                                         headers={"Authorization": f"Bearer {key}",
                                                  "User-Agent": "kaal-setup"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            return True, f"GitHub user: {d.get('login', '?')}"
        from ..models.router import PROVIDER_URLS, DEFAULT_MODELS
        url = PROVIDER_URLS.get(provider, "")
        if not url:
            return False, "ping endpoint nahi (key save ho gayi, test skip)"
        body = json.dumps({"model": DEFAULT_MODELS.get(provider, "auto"),
                           "messages": [{"role": "user", "content": "hi"}],
                           "max_tokens": 5}).encode()
        req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            json.load(r)
        return True, "key valid (ping OK)"
    except Exception as e:
        s = str(e)[:120]
        if "401" in s or "403" in s:
            return False, "auth-fail — key galat/revoked"
        if "429" in s:
            return False, "rate-limit — key sahi lag rahi, baad me try karo"
        return False, f"ping fail: {s}"

def run_setup():
    """Interactive wizard. Returns None."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm
    import getpass
    from . import palette as _pal
    from ..models.router import add_user_key, key_health
    console = Console()
    console.print(Panel("Kaal Setup — provider keys vault me (masked input, history me nahi)",
                        title=" Setup", border_style="cyan", padding=(0, 1)))
    while True:
        health = key_health()
        opts = []
        for p in PROVIDERS:
            n = len(health.get(p, []))
            opts.append((p, f"{n} keys" if n else "—"))
        opts.append(("done", "ho gaya, bahar"))
        sel = _pal.pick(opts, title="Setup — provider chuno")
        if not sel or sel == "done":
            break
        try:
            key = getpass.getpass(f"  {sel} key (masked, paste karo): ").strip()
        except Exception:
            console.print("[yellow]Masked input nahi hua (non-TTY?) — /keys add se karo.[/]")
            break
        if not key:
            continue
        console.print(f"[green]{add_user_key(sel, key)}[/]")
        try:
            if Confirm.ask(f"  [dim]Test karu ({sel} ping)?[/]", default=True):
                ok, msg = ping_key(sel, key)
                console.print(f"[green] {msg}[/]" if ok else f"[yellow] {msg}[/]")
        except (EOFError, KeyboardInterrupt):
            pass
    mark_done()
    console.print("[green]Setup done.[/]")
