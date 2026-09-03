"""Platform adapter — Termux/Linux/macOS/Windows paths, concurrency, battery note.
Same codebase, platform auto-detect. Termux pe halka, desktop pe full.
"""
import os, sys

def detect():
    try:
        if "com.termux" in os.environ.get("PREFIX", "") or "com.termux" in os.path.expanduser("~"):
            return "termux"
    except Exception:
        pass
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    return "linux"

CONCURRENCY = {"termux": 1, "linux": 4, "macos": 4, "windows": 2}

def data_dir():
    p = detect()
    if p == "termux":
        return os.path.expanduser("~/.kaal")
    if p == "macos":
        return os.path.expanduser("~/Library/Application Support/kaal")
    if p == "windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "kaal")
    xdg = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(xdg, "kaal")

def battery_note():
    if detect() != "termux":
        return ""
    for cmd in ("termux-battery-status",):
        import shutil
        if shutil.which(cmd):
            return "🔋 Termux battery API mili — low battery pe heavy task roko"
    return "🔋 Battery saver: Termux pe concurrency 1, bade task tukdo me"

def describe():
    p = detect()
    return f"⚙️ Platform: {p} | concurrency: {CONCURRENCY.get(p,1)} | data: {data_dir()}"
