"""Storage manager — quota check + auto-clean startup.
memory/*.db, logs/*, /tmp kaal* — age + size rules. Config: storage.json ya defaults.
"""
import os, time, glob

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def du_mb(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / (1024 * 1024)

def cleanup(max_mb=500, log_days=30):
    """Purane logs + tmp clean. Returns (freed_mb, notes[])."""
    notes, freed = [], 0.0
    logdir = os.path.join(REPO, "logs")
    cutoff = time.time() - log_days * 86400
    for p in glob.glob(os.path.join(logdir, "*")):
        try:
            if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                freed += os.path.getsize(p) / (1024 * 1024)
                os.remove(p)
                notes.append(f"purana log hata: {os.path.basename(p)}")
        except OSError:
            pass
    for p in glob.glob("/tmp/kaal*") + glob.glob(os.path.join(REPO, "memory", "tmp*")):
        try:
            if os.path.isfile(p) and time.time() - os.path.getmtime(p) > 86400:
                freed += os.path.getsize(p) / (1024 * 1024)
                os.remove(p)
                notes.append("tmp clean")
        except OSError:
            pass
    return round(freed, 1), notes[:5]

def startup_check(max_mb=500):
    """Startup pe quota check. Over quota to auto-clean. Returns status line."""
    from . import config_store as _cfg
    try:
        max_mb = int(_cfg.get_all()["storage"].get("max_mb", max_mb))
    except Exception:
        pass
    used = du_mb(os.path.join(REPO, "memory")) + du_mb(os.path.join(REPO, "logs"))
    if used <= max_mb:
        return f" Storage ok: {used:.1f}/{max_mb}MB"
    freed, notes = cleanup(max_mb)
    used2 = du_mb(os.path.join(REPO, "memory")) + du_mb(os.path.join(REPO, "logs"))
    extra = f" — {'; '.join(notes)}" if notes else ""
    return f" Auto-clean: {freed}MB free ({used:.1f}→{used2:.1f}/{max_mb}MB){extra}"
