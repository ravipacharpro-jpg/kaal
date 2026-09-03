"""Kaal benchmark — 12 real tasks, pass/fail + timing + delta vs last run.
Hermetic: saara kaam benchmarks/work/ me, run ke baad clean.
Run: python3 benchmarks/run.py  (repo root se)
"""
import json, os, shutil, sys, time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)
WORK = os.path.join(REPO, "benchmarks", "work")
RES = os.path.join(REPO, "benchmarks", "results.json")


def fresh():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK, exist_ok=True)
    # test-state isolation: backups/checkpoints pichle run se leak na ho
    shutil.rmtree(os.path.join(REPO, "memory", "backups"), ignore_errors=True)


TASKS = []

def task(name):
    def deco(fn):
        TASKS.append((name, fn))
        return fn
    return deco


@task("read-file")
def t1():
    from kaal.agent import run_task
    r = run_task("file read README.md", ask_cb=lambda q: True)
    return r["status"] == "done" and "Kaal" in r["summary"]

@task("list-dir")
def t2():
    from kaal.agent import run_task
    r = run_task("file list karo", ask_cb=lambda q: True)
    return r["status"] == "done" and "kaal" in r["summary"].lower()

@task("multi-agent")
def t3():
    from kaal.agent import run_task
    r = run_task("file list karo aur github repo check karo", ask_cb=lambda q: True)
    return r.get("mode") == "multi" and len(r["todos"]) == 2

@task("delete-deny")
def t4():
    from kaal.agent import run_task
    return run_task("delete x", ask_cb=lambda q: False)["status"] == "denied"

@task("code-run")
def t5():
    from kaal.agent import run_task
    r = run_task("code chalao test", ask_cb=lambda q: True)
    return "kaal ok" in r["summary"]

@task("write-edit-undo")
def t6():
    from kaal.skills import files as f
    p = os.path.join(WORK, "w.txt")
    f.write_file(p, "hello")
    f.edit_file(p, "hello", "world", lambda q: True)
    f.undo_last(p)
    return "hello" in f.read_file(p)

@task("fuzzy-syntax")
def t7():
    from kaal.skills import files as f
    p = os.path.join(WORK, "f.py")
    f.write_file(p, "x = 1  \n")
    ok = "Edit ho gayi" in f.edit_file(p, "x = 1", "x = 2", lambda q: True)
    bad = "Syntax" in f.edit_file(p, "x = 2", "x = ", lambda q: True)
    return ok and bad and "x = 2" in f.read_file(p)

@task("secret-scan")
def t8():
    from kaal.skills.secrets import scan_text
    return bool(scan_text('k = "sk-abcdefghij1234567890"')) and not scan_text("hello")

@task("checkpoint-rewind")
def t9():
    from kaal.skills import files as f
    p = os.path.join(WORK, "c.txt")
    f.write_file(p, "v1")
    f.checkpoint("b")
    f.edit_file(p, "v1", "v2", lambda q: True)
    f.rewind()
    return "v1" in f.read_file(p)

@task("plan-recipe")
def t10():
    from kaal.planner import draft
    from kaal.recipes import get
    return len(draft("code fix karo")) >= 1 and len(get("morning-review")) >= 1

@task("search-index")
def t11():
    from kaal.skills import semsearch
    semsearch.index_path("README.md")
    rows = semsearch.search("install")
    return len(rows) >= 1

@task("brain-fallback")
def t12():
    from kaal.models.router import try_chat, brain_active
    n, t = try_chat([{"role": "user", "content": "hi"}])
    return n in ("ollama_local", "rule-based") and isinstance(brain_active(), bool)


def main():
    fresh()
    try:
        results, passed = {}, 0
        for name, fn in TASKS:
            t0 = time.time()
            try:
                ok = bool(fn())
            except Exception as e:
                ok = f"ERR {e}"[:100]
            dt = round(time.time() - t0, 2)
            results[name] = {"ok": ok is True, "detail": "" if ok is True else str(ok), "secs": dt}
            if ok is True:
                passed += 1
            print(f"{'✅' if ok is True else '❌'} {name} ({dt}s)")
        prev = {}
        try:
            with open(RES, encoding="utf-8") as f:
                prev = json.load(f).get("tasks", {})
        except Exception:
            pass
        print(f"\n{passed}/{len(TASKS)} pass")
        for n, r in results.items():
            o = prev.get(n, {}).get("ok")
            if o is not None and o != r["ok"]:
                print(("📈 fixed: " if r["ok"] else "📉 broke: ") + n)
        with open(RES, "w", encoding="utf-8") as f:
            json.dump({"tasks": results, "pass": passed, "total": len(TASKS)}, f, indent=2)
    finally:
        shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()
