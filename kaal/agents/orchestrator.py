"""Orchestrator — task decompose, specialist assign, result aggregate.
Har specialist ka apna persona (role prompt) hai — legacy path me live/summary
me role dikhta hai, brain path me persona context prompt me jata hai.
Honest note: routing keyword-based hai; dimaag (reasoning) brain/LLM lagata hai.
"""

PERSONAS = {
    "coder": "Coder: pehle repo_scan/file_read se context, chote diffs, test_run se verify.",
    "researcher": "Researcher: 2-3 sources browser_fetch, facts + URLs ke saath summary.",
    "analyzer": "Analyzer: data compare karke table-style nishkarsh, andaza nahi.",
    "github_specialist": "GitHuber: repo/issues dico, numbers exact (stars, issue #).",
    "general": "Generalist: seedha kaam, short summary.",
    "minimal_change_engineer": "Minimal Change Engineer: sirf jo poocha wahi fix karo, scope creep nahi. Chhote targeted changes, bilkul minimal diff. Over-engineering mat karo.",
    "code_reviewer": "Code Reviewer: self-review pass ke liye. Security, edge cases, error handling check karo. Fail to fix karo.",
    "security_architect": "Security Architect / AppSec: code security review. SQLi, XSS, auth bypass, secrets exposure check karo. OWASP top 10 mindset.",
    "database_optimizer": "Database Optimizer: query plan, indexes, N+1 problems. Performance nishkarsh.",
    "software_architect": "Software Architect: bade refactor tasks ke liye. System design, modularity, scalability mindset.",
    "planner": "Planner: read-only planning. Pehle repo_scan/file_read se samjho, phir numbered plan likho — code/file change mat karo.",
    "explorer": "Explorer: read-only research. Grep/glob/file_read/webfetch se dhoondho, facts + paths ke saath report — change mat karo.",
}

ROLES = ("coder", "researcher", "analyzer", "github_specialist",
          "minimal_change_engineer", "code_reviewer", "security_architect",
          "database_optimizer", "software_architect", "planner", "explorer", "general")

def persona(agent):
    return PERSONAS.get(agent, PERSONAS["general"])

def classify(step):
    s = step.lower()
    if "github" in s or "repo" in s or "issue" in s or "pr " in s:
        return "github_specialist"
    if "security" in s or "auth" in s or "vuln" in s or "xss" in s or "sqli" in s or "sql" in s:
        return "security_architect"
    if "review" in s or "code review" in s or "check karo" in s:
        return "code_reviewer"
    if "database" in s or "query" in s or "index" in s or "optimize" in s:
        return "database_optimizer"
    if "architect" in s or "design" in s or "refactor" in s or "system" in s or "modular" in s or "scalab" in s:
        return "software_architect"
    if "minimal" in s or "small change" in s or "just fix" in s or "scope creep" in s:
        return "minimal_change_engineer"
    if "plan" in s or "yojana" in s or "strategy" in s or "steps batao" in s:
        return "planner"
    if "explore" in s or "dhoond" in s or "khoj" in s or "find " in s or "search" in s or "kahan hai" in s:
        return "explorer"
    if "code" in s or "python" in s or "fix" in s or "bug" in s or "function" in s:
        return "coder"
    if "research" in s or "browser" in s or "web" in s or "site" in s or "http" in s or "kya hai" in s:
        return "researcher"
    if "analyz" in s or "data" in s or "trend" in s or "compare" in s or "summary" in s:
        return "analyzer"
    return "general"

def classify_llm(step):
    """Brain mode me LLM se role chunwao; fail to keyword fallback.
    (prompt.cpp sahi tha — keyword routing reasoning nahi hai.)"""
    try:
        from ..models.router import brain_active, try_chat
        if not brain_active():
            return classify(step)
        _, txt = try_chat([
            {"role": "system", "content": "Reply with EXACTLY one word (one of these, no other text): " + "/".join(ROLES)},
            {"role": "user", "content": f"Task step: {step[:200]}"}])
        t = (txt or "").strip().lower()
        if t in ROLES:
            return t
    except Exception:
        pass
    return classify(step)

def decompose(task, smart=False):
    """Bade task ko sub-tasks me todo. Max 4 agents parallel.
    smart=True (brain mode) to LLM se role, warna keyword."""
    parts = [p.strip() for p in task.replace("aur", ",").split(",") if p.strip()]
    if len(parts) <= 1 and len(task) > 80:
        parts = [task[i:i+80] for i in range(0, len(task), 80)][:3]
    if not parts:
        parts = [task]
    jobs = []
    for p in parts[:4]:
        a = classify_llm(p) if smart else classify(p)
        jobs.append({"step": p, "agent": a, "status": "pending"})
    return jobs
