"""Autonomy levels — loop-engineering pattern (L1 report-only → L2 assisted → L3 full).
L1 (scheduled default): read-only tools, mutation sirf report.
L2: /perm allow-list honored (explicit allow chalta hai, ask/deny nahi).
L3: sab kuch — sirf explicit --unattended flag ya interactive TUI pe.
"""
MUTATING_TOOLS = {"file_write", "file_edit", "file_delete", "code_run", "bash_run",
                  "git_commit", "pr_open", "test_run"}

LEVELS = ("L1", "L2", "L3")

def get_level():
    try:
        from . import config_store as _cfg
        lv = str(_cfg.get_all().get("autonomy", {}).get("scheduled_level", "L1")).upper()
        return lv if lv in LEVELS else "L1"
    except Exception:
        return "L1"

def tool_allowed(tool_name, level, ask_cb=None, prompt=""):
    """Returns (allowed_bool, note). L1: mutating→report-only. L2: perm-based. L3: open."""
    if tool_name not in MUTATING_TOOLS:
        return True, ""
    if level == "L1":
        return False, f"L1 report-only: {tool_name} skip (report me darj)"
    if level == "L2":
        try:
            from . import config_store as _cfg
            op = {"file_write": "write_files", "file_edit": "write_files",
                  "file_delete": "delete_files", "code_run": "code_execution",
                  "bash_run": "code_execution", "git_commit": "api_calls",
                  "pr_open": "api_calls", "test_run": "code_execution"}.get(tool_name, "")
            mode = _cfg.get_perm(op) if op else "ask"
            if mode == "allow":
                return True, ""
            return False, f"L2: {tool_name} not allowed (/{op} allow nahi hai)"
        except Exception:
            return False, f"L2: {tool_name} blocked"
    return True, ""
