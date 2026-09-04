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

FOOTER_HINT = ("[dim]/endpoints /budget /memory /user /thread /trace /tree /agents /key /model /effort /ollama /schedule "
               "/perm /plan /approve /review /research /bg /fresh /ship /autopilot /recipe /plugin /voice /checkpoint /rewind /export /quit [dim]· seedha task likho[/]")

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
