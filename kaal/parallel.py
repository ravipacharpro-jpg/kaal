"""Parallel subagent engine — DAG + ordered aggregate (PC takkar track, v1).
- jobs: [{id, title, agent, needs:[ids]}]. needs khaali = independent = parallel.
- auto_graph(): risky steps (delete/edit/write/commit) chain me, read-only parallel.
- run_graph(): topological levels, level-wise ThreadPoolExecutor, results job-order me.
- v1 guarantee: writers kabhi parallel nahi (file-clash impossible by construction).
- v2 roadmap: isolated git worktrees (cwd plumbing chahiye — bada change, alag task).
"""
from concurrent.futures import ThreadPoolExecutor

WRITE_VERBS = ("delete", "edit", "write", "commit", "rm ", "push")

def is_risky(title):
    t = (title or "").lower()
    return any(v in t for v in WRITE_VERBS)

def auto_graph(steps):
    """[(title, agent)] → jobs. Risky step sabse pehle walo pe depend (chain)."""
    jobs = []
    last_risky = None
    for i, (title, agent) in enumerate(steps):
        jid = f"j{i}"
        needs = []
        if is_risky(title):
            needs = [j["id"] for j in jobs]  # sab khatm, tabhi write
            last_risky = jid
        elif last_risky:
            needs = [last_risky]  # write ke baad wale reads uske baad
        jobs.append({"id": jid, "title": title, "agent": agent, "needs": needs,
                     "status": "pending"})
    return jobs

def attach_needs(todos):
    """Existing todo dicts (in-place) pe id + needs lagao. Returns same list."""
    graph = auto_graph([(t.get("title", ""), t.get("agent", "general")) for t in todos])
    for td, g in zip(todos, graph):
        td["id"] = g["id"]
        td["needs"] = g["needs"]
    return todos

def levels(jobs):
    """Topological levels. Cycle/unknown-dep → sab sequential (safe fallback)."""
    ids = {j["id"] for j in jobs}
    for j in jobs:
        if any(n not in ids for n in j.get("needs", [])):
            return [[j["id"]] for j in jobs]
    done, rest, out = set(), {j["id"]: set(j.get("needs", [])) for j in jobs}, []
    while rest:
        ready = sorted([i for i, ns in rest.items() if ns <= done])
        if not ready:  # cycle — bacha sab sequential
            out.extend([[i] for i in sorted(rest)])
            break
        out.append(ready)
        done.update(ready)
        for i in ready:
            del rest[i]
    by_id = {j["id"]: j for j in jobs}
    return [[by_id[i] for i in lvl] for lvl in out]

def run_graph(jobs, fn, max_workers=4, cancel=None):
    """Level-wise parallel run. fn(job) → (line, stop_bool).
    Returns [lines] job-order me. cancel Event set → wind-down."""
    order = [j["id"] for j in jobs]
    results = {}
    stopped = False
    for lvl in levels(jobs):
        if stopped or (cancel is not None and cancel.is_set()):
            break
        if len(lvl) > 1 and max_workers > 1:
            with ThreadPoolExecutor(max_workers=min(max_workers, len(lvl))) as ex:
                for job, (line, stop) in zip(lvl, ex.map(fn, lvl)):
                    results[job["id"]] = (line, stop)
                    if stop:
                        stopped = True
                        break
        else:
            for job in lvl:
                if cancel is not None and cancel.is_set():
                    stopped = True
                    break
                line, stop = fn(job)
                results[job["id"]] = (line, stop)
                if stop:
                    stopped = True
                    break
    return [results[i][0] for i in order if i in results]
