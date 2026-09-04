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

# Static matrix: chhota kam khaye, bada zyada (user philosophy).
# True = full, False = nahi, "capped"/"cron" = limited mode.
MATRIX = {
    "termux": {"docker": False, "lsp_server": False, "daemon_service": "cron",
               "big_index": "capped", "voice_mic": "termux-api",
               "parallel": 1, "note": "halka mode: concurrency 1, index cap, cron-jobs"},
    "linux": {"docker": "if-installed", "lsp_server": "if-installed",
              "daemon_service": "systemd", "big_index": True, "voice_mic": False,
              "parallel": 4, "note": "full mode"},
    "macos": {"docker": "if-installed", "lsp_server": "if-installed",
              "daemon_service": "launchd-manual", "big_index": True, "voice_mic": False,
              "parallel": 4, "note": "full mode (docker desktop chahiye)"},
    "windows": {"docker": "if-installed", "lsp_server": "if-installed",
                "daemon_service": "task-scheduler-manual", "big_index": True,
                "voice_mic": False, "parallel": 2,
                "note": "LSP stdio-select nahi — diagnostics py_compile fallback"},
}

def probe():
    """Runtime binary probes (actual, not assumed). Returns {name: bool}."""
    import shutil
    out = {}
    for name in ("docker", "gh", "ollama", "pyright", "pyright-langserver",
                 "termux-api", "termux-job-scheduler", "pip-audit", "node"):
        try:
            out[name] = shutil.which(name) is not None
        except Exception:
            out[name] = False
    return out

def capabilities():
    """Static matrix + live probes merge. TUI /platform aur startup ke liye."""
    p = detect()
    caps = dict(MATRIX.get(p, MATRIX["linux"]))
    caps["platform"] = p
    caps["probes"] = probe()
    caps["docker"] = bool(caps["docker"] == True or
                          (caps["docker"] == "if-installed" and caps["probes"]["docker"]))
    return caps

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
            return " Termux battery API mili — low battery pe heavy task roko"
    return " Battery saver: Termux pe concurrency 1, bade task tukdo me"

def describe():
    p = detect()
    return f" Platform: {p} | concurrency: {CONCURRENCY.get(p,1)} | data: {data_dir()}"
