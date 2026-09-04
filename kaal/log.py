"""App log — human-readable rotating file log (logs/kaal.log).
trace.jsonl = machine events; kaal.log = human diagnosis (issue kahan aaya).
Secrets auto-redacted (sk-*, ghp_*, Bearer, password=). 512KB x 3 backups.
"""
import logging
import os
import re
from logging.handlers import RotatingFileHandler

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs", "kaal.log"))
MAX_BYTES = 512 * 1024
BACKUPS = 3

REDACT = [
    (re.compile(r"sk-[A-Za-z0-9\-_]{8,}"), "sk-***"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{8,}"), "ghp-***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{8,}"), "Bearer ***"),
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*[^\\s,}]+"), r"\1=***"),
]

_logger = None

def _redact(msg):
    try:
        s = str(msg)
        for pat, rep in REDACT:
            s = pat.sub(rep, s)
        return s
    except Exception:
        return "*** log-format-error ***"

class _RedactFilter(logging.Filter):
    def filter(self, record):
        try:
            record.msg = _redact(record.getMessage())
            record.args = ()
        except Exception:
            pass
        return True

def get_logger(name="kaal"):
    """Singleton logger (file + null-safe). Kabhi crash nahi karega."""
    global _logger
    if _logger is not None:
        return _logger
    lg = logging.getLogger(name)
    lg.setLevel(logging.DEBUG)
    lg.addFilter(_RedactFilter())
    try:
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        fh = RotatingFileHandler(PATH, maxBytes=MAX_BYTES, backupCount=BACKUPS,
                                 encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                                          datefmt="%Y-%m-%d %H:%M:%S"))
        lg.addHandler(fh)
    except Exception:
        lg.addHandler(logging.NullHandler())
    lg.propagate = False
    _logger = lg
    return lg

def tail(n=30):
    """Akhri N lines (TUI /logs ke liye)."""
    try:
        with open(PATH, encoding="utf-8", errors="replace") as f:
            return f.readlines()[-n:]
    except Exception:
        return []

def info(msg):
    try:
        get_logger().info(msg)
    except Exception:
        pass

def warn(msg):
    try:
        get_logger().warning(msg)
    except Exception:
        pass

def error(msg):
    try:
        get_logger().error(msg)
    except Exception:
        pass
