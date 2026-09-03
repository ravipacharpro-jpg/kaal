"""Unified tool registry — LLM brain inhe JSON se call karta hai.
Har tool: name, desc, params, fn. Output summary-truncated (no dump).
"""
from . import files as _f
from . import code as _c
from . import browser as _b
from . import dev as _d
from ..mcp import github as _gh
from ..memory.store import recent as _recent


def _t_file_read(a):
    return _f.read_file(a.get("path", ""), 3000)[:1500]

def _t_file_list(a):
    return _f.list_dir(a.get("path", "."))[:500]

def _t_file_write(a):
    return _f.write_file(a.get("path", ""), a.get("content", ""))[:200]

def _t_file_edit(a):
    return _f.edit_file(a.get("path", ""), a.get("old", ""),
                        a.get("new", ""), a.get("_ask"))[:600]

def _t_file_delete(a):
    return _f.delete_path(a.get("path", ""), a.get("_ask"))[:200]

def _t_code_run(a):
    return _c.run_python(a.get("code", ""), int(a.get("timeout", 30)))[:800]

def _t_browser_fetch(a):
    return _b.fetch_text(a.get("url", ""))[:1500]

def _t_github_repo(a):
    return _gh.repo_info(a.get("repo", ""), a.get("token", ""))[:400]

def _t_github_issues(a):
    return _gh.list_issues(a.get("repo", ""), a.get("token", ""))[:500]

def _t_memory_recall(a):
    rows = _recent(int(a.get("n", 5)))
    return " | ".join(f"{t[:50]}→{s[:80]}" for t, s in rows)[:800] or "memory khaali"

def _t_repo_scan(a):
    return _d.repo_map(a.get("path", "."))[:2000]

def _t_test_run(a):
    return _d.test_run(a.get("cmd", "python3 -m pytest -q"))[:1000]

def _t_pr_open(a):
    ask = a.get("_ask")
    if ask and not ask(f"PR kholu: {a.get('title','kaal: auto fix')[:80]}?"):
        return "PR cancel — permission deny"
    return _d.pr_open(a.get("title", "kaal: auto fix"), a.get("body", ""))[:300]

TOOLS = [
    {"name": "file_read", "desc": "File padho", "params": "path",
     "fn": _t_file_read},
    {"name": "file_list", "desc": "Folder list karo", "params": "path?",
     "fn": _t_file_list},
    {"name": "file_write", "desc": "Nayi file likho (overwrite)", "params": "path, content",
     "fn": _t_file_write},
    {"name": "file_edit", "desc": "File me old text ko new se badlo (diff preview + approval)",
     "params": "path, old, new", "fn": _t_file_edit, "needs_approval": True},
    {"name": "file_delete", "desc": "File/folder delete (approval must)",
     "params": "path", "fn": _t_file_delete, "needs_approval": True},
    {"name": "code_run", "desc": "Python sandbox me chalao (30s)", "params": "code",
     "fn": _t_code_run},
    {"name": "browser_fetch", "desc": "URL ka text nikalo", "params": "url",
     "fn": _t_browser_fetch},
    {"name": "github_repo", "desc": "GitHub repo info", "params": "repo (owner/name)",
     "fn": _t_github_repo},
    {"name": "github_issues", "desc": "Repo ke open issues", "params": "repo",
     "fn": _t_github_issues},
    {"name": "memory_recall", "desc": "Purane tasks/summary dekho", "params": "n?",
     "fn": _t_memory_recall},
    {"name": "repo_scan", "desc": "Codebase structure map karo", "params": "path?",
     "fn": _t_repo_scan},
    {"name": "test_run", "desc": "Tests chalao aur PASS/FAIL summary lo",
     "params": "cmd?", "fn": _t_test_run},
    {"name": "pr_open", "desc": "gh CLI se PR kholo", "params": "title, body?",
     "fn": _t_pr_open, "needs_approval": True},
]

BY_NAME = {t["name"]: t for t in TOOLS}

def spec_text():
    lines = ["TOOLS (JSON call karo):"]
    for t in TOOLS:
        lines.append(f'- {t["name"]}({t["params"]}): {t["desc"]}')
    return "\n".join(lines)
