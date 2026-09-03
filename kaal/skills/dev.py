"""Dev skills — codebase scan, test run, PR open (Claude Code style).
Sab sandboxed + timeout + summary only.
"""
import os, subprocess, shutil

SKIP = {".git", "__pycache__", "node_modules", ".venv", ".nexus", "dist", "build"}

def repo_map(root=".", max_files=60):
    """Codebase structure summary: tree + file sizes. Scam-safe paths."""
    root = os.path.abspath(os.path.expanduser(root))
    home = os.path.expanduser("~")
    if ".." in os.path.relpath(root, home).split(os.sep):
        return "Unsafe path"
    out = []
    n = 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        level = os.path.relpath(dirpath, root).count(os.sep)
        if level > 3:
            dirs[:] = []
            continue
        for f in sorted(files)[:30]:
            p = os.path.join(dirpath, f)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            out.append(f"{'  '*level}{os.path.relpath(p, root)} ({sz//1024}KB)")
            n += 1
            if n >= max_files:
                return "\n".join(out)[:2000] + "\n... (aur files)"
    return "\n".join(out)[:2000] if out else "Khaali folder"

def test_run(cmd="python3 -m pytest -q", timeout=120):
    """Tests chalao. Output truncate. Fail to summary + hint."""
    parts = cmd.split()[:10]
    if parts[0] not in ("python3", "python", "pytest", "npm", "npx", "go"):
        return "Block: ye command allowed nahi"
    try:
        r = subprocess.run(parts, capture_output=True, text=True, timeout=timeout)
        tail = (r.stdout + r.stderr)[-1000:]
        status = "PASS" if r.returncode == 0 else f"FAIL({r.returncode})"
        return f"{status}: {tail[:800]}"
    except subprocess.TimeoutExpired:
        return f"Timeout {timeout}s"
    except FileNotFoundError:
        return "Command mili nahi (pytest installed?)"
    except Exception as e:
        return f"Error: {e}"[:200]

def pr_open(title, body="", base="main"):
    """gh CLI se PR kholo. gh nahi to reason."""
    if shutil.which("gh") is None:
        return "gh CLI nahi mili — PR manual kholo"
    try:
        r = subprocess.run(["gh", "pr", "create", "--title", title[:100],
                            "--body", body[:500], "--base", base],
                           capture_output=True, text=True, timeout=30)
        out = (r.stdout + r.stderr).strip()[:300]
        return out if r.returncode == 0 else f"PR fail: {out[:200]}"
    except Exception as e:
        return f"Error: {e}"[:200]
