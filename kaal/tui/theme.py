"""Kaal theme — OpenCode-style premium look.
Clean monochrome + single cyan accent. Subtle, premium.
"""
ACCENT = "cyan"
OK = "green"
WARN = "yellow"
ERR = "red"
DIM = "dim"
BRIGHT = "bright_white"
MAGENTA = "magenta"

NAME = "kaal"
VERSION = "v0.6.0"
TAGLINE = "autonomous agent · ahead of time"

FOOTER_HINT = ("[dim]/palette /dashboard /endpoints /platform /budget /memory /user /thread /trace /tree /agents /key /model /effort /ollama /schedule "
               "/perm /plan /approve /review /research /bg /fresh /ship /autopilot /cache /comment-zh /reflect /recipe /plugin /voice /checkpoint /rewind /export /logs /quit [dim]· seedha task likho[/]")

def load_accent():
    """config/tui.json se saved accent lao (global, live)."""
    global ACCENT
    try:
        import json
        import os
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "tui.json"))
        with open(p, encoding="utf-8") as f:
            a = (json.load(f) or {}).get("accent", "")
        if a in ("cyan", "green", "magenta", "yellow", "red", "blue"):
            ACCENT = a
    except Exception:
        pass
    return ACCENT

ZOOMS = ("compact", "normal", "large")

def _tui_file():
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "config", "tui.json"))

def get_zoom():
    """UI density: compact|normal|large. Terminal font app se nahi badalta —
    ye spacing/columns badalta hai (honest zoom). Default normal."""
    try:
        import json
        with open(_tui_file(), encoding="utf-8") as f:
            z = (json.load(f) or {}).get("zoom", "normal")
        return z if z in ZOOMS else "normal"
    except Exception:
        return "normal"

def set_zoom(name):
    name = str(name or "").lower()
    if name == "in":
        order = list(ZOOMS)
        name = order[min(2, order.index(get_zoom()) + 1)]
    elif name == "out":
        order = list(ZOOMS)
        name = order[max(0, order.index(get_zoom()) - 1)]
    if name not in ZOOMS:
        return f"Use: /zoom in|out|compact|normal|large (current: {get_zoom()})"
    try:
        import json
        import os
        p = _tui_file()
        d = {}
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f) or {}
        except Exception:
            pass
        d["zoom"] = name
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception:
        pass
    return f"Zoom: {name} (spacing + columns) — font terminal se badlo"

def zoom_padding():
    """Panel padding per zoom level."""
    return {"compact": (0, 0), "normal": (0, 1), "large": (1, 2)}.get(get_zoom(), (0, 1))

def wide_threshold():
    """Columns-vs-stacked width cutoff per zoom."""
    return {"compact": 80, "normal": 100, "large": 130}.get(get_zoom(), 100)

SHORT_HINT = "[dim]/palette · /dashboard · /quit — seedha task likho[/]"

def clean_mode():
    """Nexus-style clean screen: technical noise off (estimate, startup, long hints).
    Default ON. /clean toggles."""
    try:
        import json
        with open(_tui_file(), encoding="utf-8") as f:
            return bool((json.load(f) or {}).get("clean", True))
    except Exception:
        return True

def set_clean(on):
    try:
        import json
        import os
        p = _tui_file()
        d = {}
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f) or {}
        except Exception:
            pass
        d["clean"] = bool(on)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception:
        pass
    return f"Clean screen: {'on' if on else 'off'}"
