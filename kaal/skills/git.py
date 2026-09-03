"""Git skill — Aider/AICommits style: status, diff summary, auto-commit.
Repo root auto-detect, safe args only (no push without approval).
"""
import subprocess

def _git(args, timeout=20):
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()[:1500]
    except FileNotFoundError:
        return 1, "git nahi mili"
    except Exception as e:
        return 1, f"Error: {e}"[:150]

def status():
    code, out = _git(["status", "--short"])
    if code != 0:
        return out
    return out or "Working tree clean ✅"

def diff_summary():
    code, out = _git(["diff", "--stat"])
    if code != 0:
        return out
    code2, out2 = _git(["diff", "--", "."])
    lines = [l for l in out2.splitlines() if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    return (out + "\n" + "\n".join(lines[:20]))[:1200] or "Koi change nahi"

def auto_commit(message="", ask_cb=None):
    code, st = _git(["status", "--short"])
    if code != 0:
        return st
    if not st:
        return "Commit ke liye koi change nahi"
    if not message:
        code2, d = _git(["diff", "--stat"])
        files = " ".join(l.split("|")[0].strip().split("/")[-1] for l in d.splitlines()[:4] if "|" in l)
        message = f"kaal: update {files}"[:100] or "kaal: auto commit"
    if ask_cb and not ask_cb(f"Commit karu?\n{message}\n{st[:300]}"):
        return "Commit cancel — permission deny"
    _git(["add", "-A"])
    code3, out3 = _git(["commit", "-m", message[:100]])
    return out3[:300] if code3 == 0 else f"Commit fail: {out3[:200]}"
