"""MCP registry — on-demand load, idle unload (lightweight)."""
import time

SERVERS = {"browser": {"cmd": "npx @playwright/mcp --headless", "on_demand": True},
           "github": {"cmd": "internal", "on_demand": True}}
_loaded = {}

def load(name):
    s = SERVERS.get(name)
    if not s:
        return f"MCP {name} mili nahi"
    _loaded[name] = time.time()
    return f"MCP {name} load ho gayi"

def unload_idle(max_idle=120):
    now = time.time()
    for n in [k for k, t in _loaded.items() if now - t > max_idle]:
        del _loaded[n]
    return f"Active MCP: {list(_loaded) if _loaded else 'koi nahi'}"

def active():
    return list(_loaded)
