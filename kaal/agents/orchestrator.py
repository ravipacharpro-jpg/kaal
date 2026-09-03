"""Orchestrator — task decompose, specialist assign, result aggregate.
Har specialist ka apna persona (role prompt) hai — legacy path me live/summary
me role dikhta hai, brain path me persona context prompt me jata hai.
Honest note: routing keyword-based hai; dimaag (reasoning) brain/LLM lagata hai.
"""

PERSONAS = {
    "coder": "Coder: pehle repo_scan/file_read se context, chhote diffs, test_run se verify.",
    "researcher": "Researcher: 2-3 sources browser_fetch, facts + URLs ke saath summary.",
    "analyzer": "Analyzer: data compare karke table-style nishkarsh, andaza nahi.",
    "github_specialist": "GitHuber: repo/issues dico, numbers exact (stars, issue #).",
    "general": "Generalist: seedha kaam, short summary.",
}

def persona(agent):
    return PERSONAS.get(agent, PERSONAS["general"])

def classify(step):
    s = step.lower()
    if "github" in s or "repo" in s or "issue" in s or "pr " in s:
        return "github_specialist"
    if "code" in s or "python" in s or "fix" in s or "bug" in s or "function" in s:
        return "coder"
    if "research" in s or "browser" in s or "web" in s or "site" in s or "http" in s or "kya hai" in s:
        return "researcher"
    if "analyz" in s or "data" in s or "trend" in s or "compare" in s or "summary" in s:
        return "analyzer"
    return "general"

def decompose(task):
    """Bade task ko sub-tasks me todo. Max 4 agents parallel."""
    parts = [p.strip() for p in task.replace("aur", ",").split(",") if p.strip()]
    if len(parts) <= 1 and len(task) > 80:
        parts = [task[i:i+80] for i in range(0, len(task), 80)][:3]
    if not parts:
        parts = [task]
    jobs = []
    for p in parts[:4]:
        jobs.append({"step": p, "agent": classify(p), "status": "pending"})
    return jobs
