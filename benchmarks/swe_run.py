"""SWE-bench-style local harness — full dataset nahi, single-instance runner.
Temp git worktree @ base_commit me test_cmd chalao, PASS/FAIL report karo.
Docker nahi chahiye (PC pe docker isolation alag se); Termux-safe subprocess.
"""
import os, shutil, subprocess, tempfile, time

def _git(cwd, args, timeout=30):
    try:
        r = subprocess.run(["git", "-C", cwd] + args, capture_output=True,
                           text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()[:2000]
    except FileNotFoundError:
        return 1, "git nahi mili"
    except Exception as e:
        return 1, f"Error: {e}"[:200]

def run_instance(repo=".", base_commit="HEAD", test_cmd="python3 -m pytest -q", timeout=300):
    """Returns dict: status PASS|FAIL|ERROR, output tail, secs.
    Repo dirty ho to worktree alag banata hai — working tree untouched."""
    repo = os.path.abspath(repo)
    if _git(repo, ["rev-parse", "--git-dir"])[0] != 0:
        return {"status": "ERROR", "output": "git repo nahi", "secs": 0}
    wt = tempfile.mkdtemp(prefix="kaal-swe-")
    t0 = time.time()
    try:
        code, out = _git(repo, ["worktree", "add", "--detach", wt, base_commit])
        if code != 0:
            return {"status": "ERROR", "output": out[:500], "secs": round(time.time() - t0, 2)}
        parts = test_cmd.split()[:12]
        try:
            r = subprocess.run(parts, cwd=wt, capture_output=True, text=True, timeout=timeout)
            tail = (r.stdout + r.stderr)[-1500:]
            st = "PASS" if r.returncode == 0 else "FAIL"
            return {"status": st, "output": tail, "secs": round(time.time() - t0, 2)}
        except subprocess.TimeoutExpired:
            return {"status": "ERROR", "output": f"Timeout {timeout}s", "secs": round(time.time() - t0, 2)}
        except FileNotFoundError:
            return {"status": "ERROR", "output": "test command nahi mili", "secs": round(time.time() - t0, 2)}
    finally:
        _git(repo, ["worktree", "remove", "--force", wt])
        shutil.rmtree(wt, ignore_errors=True)
