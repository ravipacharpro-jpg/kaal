"""Structured workflows — OpenCode-style /fresh /ship /autopilot ke pure helpers.
TUI sirf thin wiring karta hai; logic yahan taaki test ho sake.
"""
import re, time

def fresh_branch(ticket):
    """Ticket se safe branch name banao: lowercase, [a-z0-9-] only."""
    slug = re.sub(r"[^a-z0-9]+", "-", ticket.lower()).strip("-")[:40] or "task"
    return f"kaal/{slug}"

def fresh_plan(ticket):
    """5-phase cycle ke steps do (understand→plan→execute→verify→handoff)."""
    t = ticket[:80]
    return [f"understand: {t} — repo_scan/file_read se context",
            f"plan: {t} — numbered steps likho",
            f"execute: {t} — chote diffs, test_run se verify",
            f"verify: {t} — review + lint + tests green",
            f"handoff: {t} — 3-line summary"]

def autopilot_pick(jobs, max_jobs=3):
    """Due jobs me se pehle max_jobs lo (budget burn guard). Pure function."""
    return [j.get("task", "")[:200] for j in (jobs or [])[:max_jobs] if j.get("task")]

def ship_message(plan_text=""):
    """Squash-commit message banao (plan first line se)."""
    first = (plan_text.strip().splitlines() or ["kaal: ship"])[0][:72]
    return first or "kaal: ship"
