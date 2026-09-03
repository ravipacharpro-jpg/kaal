"""Code skill — docker sandbox (PC, opt-in) ya subprocess (default/Termux)."""
import subprocess, sys

TIMEOUT = 30
BLOCKED = ("os.system", "subprocess", "socket", "__import__", "eval(", "exec(")

def run_python(code, timeout=TIMEOUT):
    for b in BLOCKED:
        if b in code:
            return f"Block: {b} sandbox me allowed nahi"
    try:
        from . import sandbox as _sb
        if _sb.enabled() and _sb.available():
            return "[docker] " + _sb.run_docker(code, timeout)
    except Exception:
        pass
    try:
        r = subprocess.run([sys.executable, "-c", code[:4000]],
                           capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr).strip()[:800]
        return out if out else f"Exit {r.returncode}, output khaali"
    except subprocess.TimeoutExpired:
        return f"Timeout {timeout}s — code bahut lamba chala"
    except Exception as e:
        return f"Error: {e}"[:200]
