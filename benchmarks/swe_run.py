"""SWE-bench-style local harness — dataset batch + grading.
Temp git worktree @ base_commit → patch lagao → FAIL_TO_PASS + PASS_TO_PASS chalao.
Docker nahi chahiye (PC pe docker isolation alag se); Termux-safe subprocess.
Official SWE-bench dataset nahi — apna JSON format (neeche), lekin grading logic same:
F2P pre-patch FAIL + post-patch PASS, P2P post-patch PASS = resolved.
"""
import json
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
        code, out = (1, "not tried")
        for _ in range(2):
            _git(repo, ["worktree", "prune"])
            code, out = _git(repo, ["worktree", "add", "--detach", wt, base_commit])
            if code == 0:
                break
            _git(repo, ["worktree", "remove", "--force", wt])
            shutil.rmtree(wt, ignore_errors=True)
            os.makedirs(wt, exist_ok=True)
        if code != 0:
            return {"status": "ERROR", "output": out[:500], "secs": round(time.time() - t0, 2)}
        parts = test_cmd.split()[:12]
        try:
            r = subprocess.run(parts, cwd=wt, capture_output=True, text=True, timeout=timeout)
            tail = (r.stdout + r.stderr)[-1500:]
            if r.returncode != 0 and "No module named pytest" in tail:
                st = "ERROR"
                tail = "pytest installed nahi — pip install -r requirements-dev.txt. " + tail[-300:]
            else:
                st = "PASS" if r.returncode == 0 else "FAIL"
            return {"status": st, "output": tail, "secs": round(time.time() - t0, 2)}
        except subprocess.TimeoutExpired:
            return {"status": "ERROR", "output": f"Timeout {timeout}s", "secs": round(time.time() - t0, 2)}
        except FileNotFoundError:
            return {"status": "ERROR", "output": "test command nahi mili", "secs": round(time.time() - t0, 2)}
    finally:
        _git(repo, ["worktree", "remove", "--force", wt])
        shutil.rmtree(wt, ignore_errors=True)

def _run_cmd(wt, cmd, timeout):
    """Ek test command chalao → (PASS|FAIL|ERROR, tail).
    PYTHONDONTWRITEBYTECODE=1 taaki stale __pycache__ (same-size patch +
    coarse mtime) post-patch run me purana bytecode na chalaye."""
    parts = cmd.split()[:12]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        r = subprocess.run(parts, cwd=wt, capture_output=True, text=True,
                           timeout=timeout, env=env)
        tail = (r.stdout + r.stderr)[-1500:]
        if r.returncode != 0 and "No module named pytest" in tail:
            return "ERROR", ("pytest installed nahi — pip install -r requirements-dev.txt. "
                             + tail[-300:])
        return ("PASS" if r.returncode == 0 else "FAIL"), tail
    except subprocess.TimeoutExpired:
        return "ERROR", f"Timeout {timeout}s"
    except FileNotFoundError:
        return "ERROR", "test command nahi mili"
    except Exception as e:
        return "ERROR", f"Error: {e}"[:200]

def _clear_pycache(wt):
    """Worktree ke stale .pyc hatao (patch ke baad zaroori)."""
    for dp, ds, fs in os.walk(wt):
        if "__pycache__" in ds:
            shutil.rmtree(os.path.join(dp, "__pycache__"), ignore_errors=True)
            ds.remove("__pycache__")

def apply_patch(wt, patch_text):
    """Unified diff worktree me lagao. Returns (ok, msg)."""
    if not (patch_text or "").strip():
        return True, "koi patch nahi — baseline only"
    pf = os.path.join(wt, ".kaal-swe.patch")
    try:
        with open(pf, "w", encoding="utf-8") as f:
            f.write(patch_text)
        code, out = _git(wt, ["apply", "--whitespace=fix", ".kaal-swe.patch"])
        try:
            os.remove(pf)
        except OSError:
            pass
        return (code == 0), out[:300] if code != 0 else "patch applied"
    except Exception as e:
        return False, f"Error: {e}"[:200]

def grade_instance(inst, timeout=300):
    """Ek SWE instance grade karo. inst keys:
    id, repo, base_commit, patch (optional), fail_to_pass [cmds], pass_to_pass [cmds].
    Returns dict with resolved True/False + detail."""
    iid = str(inst.get("id", "?"))
    repo = os.path.abspath(inst.get("repo", "."))
    base = inst.get("base_commit", "HEAD")
    f2p = inst.get("fail_to_pass", ["python3 -m pytest -q"])
    p2p = inst.get("pass_to_pass", [])
    t0 = time.time()
    if _git(repo, ["rev-parse", "--git-dir"])[0] != 0:
        return {"id": iid, "resolved": False, "status": "ERROR", "detail": "git repo nahi"}
    wt = tempfile.mkdtemp(prefix="kaal-swe-")
    try:
        code, out = (1, "not tried")
        for _ in range(2):  # transient git-lock flake guard (slow storage)
            _git(repo, ["worktree", "prune"])
            code, out = _git(repo, ["worktree", "add", "--detach", wt, base])
            if code == 0:
                break
            _git(repo, ["worktree", "remove", "--force", wt])
            shutil.rmtree(wt, ignore_errors=True)
            os.makedirs(wt, exist_ok=True)
        if code != 0:
            return {"id": iid, "resolved": False, "status": "ERROR",
                    "detail": out[:300]}
        pre = {}
        for cmd in f2p:
            st, _ = _run_cmd(wt, cmd, timeout)
            pre[cmd] = st
        ok, msg = apply_patch(wt, inst.get("patch", ""))
        if not ok:
            return {"id": iid, "resolved": False, "status": "ERROR",
                    "detail": f"patch fail: {msg}", "pre": pre}
        _clear_pycache(wt)  # stale bytecode guard (same-size patch + coarse mtime)
        post_f2p, post_p2p, outs = {}, {}, {}
        for cmd in f2p:
            st, tail = _run_cmd(wt, cmd, timeout)
            post_f2p[cmd] = st
            outs[cmd] = tail[-500:]
        for cmd in p2p:
            st, tail = _run_cmd(wt, cmd, timeout)
            post_p2p[cmd] = st
            outs[cmd] = tail[-500:]
        trivial = all(v == "PASS" for v in pre.values())
        resolved = (all(v == "PASS" for v in post_f2p.values())
                    and all(v == "PASS" for v in post_p2p.values())
                    and not trivial)
        return {"id": iid, "resolved": resolved, "status": "graded",
                "trivial": trivial, "pre": pre, "post_f2p": post_f2p,
                "post_p2p": post_p2p, "patch": msg,
                "secs": round(time.time() - t0, 2)}
    finally:
        _git(repo, ["worktree", "remove", "--force", wt])
        shutil.rmtree(wt, ignore_errors=True)

def load_dataset(path):
    """JSON file se instance list lao: [{id, repo, base_commit, patch, fail_to_pass, pass_to_pass}].
    HuggingFace 'datasets' lib ho + network ho to hub se bhi (SWE-bench name se)."""
    if isinstance(path, list):
        return path
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else d.get("instances", [])
    try:
        from datasets import load_dataset as _hub
        ds = _hub(path, split="test")
        return [dict(r) for r in ds]
    except Exception as e:
        raise ValueError(f"dataset nahi mila (file ya hub): {e}"[:200])

def run_dataset(path, timeout=300, out=""):
    """Poora dataset chalao → summary print + results JSON. Returns (resolved, total)."""
    insts = load_dataset(path)
    results = []
    for inst in insts:
        r = grade_instance(inst, timeout=timeout)
        results.append(r)
        mark = "PASS" if r["resolved"] else "fail"
        print(f"[{mark}] {r['id']} ({r.get('secs', 0)}s)")
    done = sum(1 for r in results if r["resolved"])
    print(f"Resolved: {done}/{len(results)}")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    return done, len(results)

if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) < 2:
        print("Use: python3 benchmarks/swe_run.py <dataset.json> [--timeout N] [--out results.json]")
        print("Instance: {id, repo, base_commit, patch, fail_to_pass[], pass_to_pass[]}")
        raise SystemExit(1)
    _to, _out = 300, ""
    _args = _sys.argv[2:]
    if "--timeout" in _args:
        _to = int(_args[_args.index("--timeout") + 1])
    if "--out" in _args:
        _out = _args[_args.index("--out") + 1]
    run_dataset(_sys.argv[1], timeout=_to, out=_out)
