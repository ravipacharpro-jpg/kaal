"""Code skill — sandboxed python subprocess, timeout, output truncate (no dump)."""
import subprocess, sys

TIMEOUT = 30
BLOCKED = ("os.system", "subprocess", "socket", "__import__", "eval(", "exec(")

def run_python(code, timeout=TIMEOUT):
    for b in BLOCKED:
        if b in code:
            return f"Block: {b} sandbox me allowed nahi"
    try:
        r = subprocess.run([sys.executable, "-c", code[:4000]],
                           capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr).strip()[:800]
        return out if out else f"Exit {r.returncode}, output khaali"
    except subprocess.TimeoutExpired:
        return f"Timeout {timeout}s — code bahut lamba chala"
    except Exception as e:
        return f"Error: {e}"[:200]
