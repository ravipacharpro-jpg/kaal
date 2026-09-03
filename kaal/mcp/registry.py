"""MCP registry — on-demand load, idle unload (lightweight).
browser: Playwright MCP spawn try (npx), na mile to internal light-fetch fallback.
github: internal API client (token optional).
"""
import shutil, subprocess, time

SERVERS = {"browser": {"cmd": ["npx", "@playwright/mcp", "--headless"], "on_demand": True},
           "github": {"cmd": "internal", "on_demand": True}}
_loaded = {}
_procs = {}

def _spawn_browser():
    """Playwright MCP server spawn try karo. Na chale to (False, reason)."""
    if shutil.which("npx") is None:
        return False, "npx nahi mila — light-fetch fallback"
    try:
        p = subprocess.Popen(["npx", "-y", "@playwright/mcp@latest", "--headless"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        if p.poll() is None:
            _procs["browser"] = p
            return True, "playwright MCP live"
        return False, "spawn fail — light-fetch fallback"
    except Exception as e:
        return False, f"{e}"[:100]

def load(name):
    s = SERVERS.get(name)
    if not s:
        return f"MCP {name} mili nahi"
    if name == "browser" and "browser" not in _procs:
        ok, msg = _spawn_browser()
        _loaded[name] = {"ts": time.time(), "mode": "playwright" if ok else "light-fetch"}
        return f"MCP browser: {msg}"
    _loaded[name] = {"ts": time.time(), "mode": "internal"} if name != "browser" else _loaded.get(name, {"ts": time.time(), "mode": "light-fetch"})
    if isinstance(_loaded[name], dict):
        _loaded[name]["ts"] = time.time()
    else:
        _loaded[name] = time.time()
    return f"MCP {name} load ho gayi"

def _ts(v):
    return v.get("ts", 0) if isinstance(v, dict) else v

def unload_idle(max_idle=120):
    now = time.time()
    for n in [k for k, t in _loaded.items() if now - _ts(t) > max_idle]:
        del _loaded[n]
        p = _procs.pop(n, None)
        if p:
            try: p.terminate()
            except Exception: pass
    act = list(_loaded) if _loaded else "koi nahi"
    return f"Active MCP: {act}"

def active():
    return list(_loaded)

def mode(name):
    v = _loaded.get(name)
    return v.get("mode", "?") if isinstance(v, dict) else "legacy"
