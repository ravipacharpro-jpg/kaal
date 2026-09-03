"""Docker sandbox — OpenHands style, optional. Linux/macOS/Windows pe agar
docker hai aur config me on hai to code container me (no network, mem limit).
Termux pe hamesha subprocess (docker possible nahi).
"""
import shutil, subprocess

IMAGE = "python:3.14-slim"

def available():
    import sys
    if sys.platform == "android":
        return False
    try:
        if "com.termux" in __import__("os").environ.get("PREFIX", ""):
            return False
    except Exception:
        pass
    return shutil.which("docker") is not None

def enabled():
    try:
        from .. import config_store as _cfg
        return bool(_cfg.get_all().get("sandbox", {}).get("docker", False))
    except Exception:
        return False

def run_docker(code, timeout=30):
    try:
        r = subprocess.run(
            ["docker", "run", "--rm", "--network", "none",
             "--memory", "256m", "--cpus", "1.0",
             "-i", IMAGE, "python3", "-c", code[:4000]],
            capture_output=True, text=True, timeout=timeout + 15)
        out = (r.stdout + r.stderr).strip()[:800]
        return out if out else f"Exit {r.returncode}, output khaali"
    except subprocess.TimeoutExpired:
        return f"Timeout {timeout}s (docker)"
    except Exception as e:
        return f"Docker fail, subprocess fallback: {e}"[:150]
