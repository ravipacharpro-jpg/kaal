"""Kaal config defaults — platform aware, Termux-safe."""
import sys, platform

def detect_platform():
    s = sys.platform
    lib = platform.libc_ver() if hasattr(platform, "libc_ver") else ("", "")
    try:
        import os
        if "com.termux" in os.environ.get("PREFIX", "") or "com.termux" in os.path.expanduser("~"):
            return "termux"
    except Exception:
        pass
    if s == "darwin":
        return "macos"
    if s.startswith("win"):
        return "windows"
    return "linux"

DEFAULTS = {
    "agent": {"name": "kaal", "version": "0.1.0", "autonomy": "full_with_permissions",
              "max_iterations": 10, "concurrency": 1},
    "model": {"default": "omniroute/auto",
              "fallback_chain": ["groq_free", "openrouter_free", "ollama_local"],
              "economy_policy": "auto/smart", "temperature": 0.7},
    "economy": {"daily_budget": 5000, "per_task_budget": 500, "policy": "auto/smart"},
    "permissions": {"delete_files": "ask", "browser": "ask",
                    "code_execution": "ask", "secrets": "ask", "api_calls": "approved"},
    "tui": {"library": "rich", "colors": True, "status_bar": True,
            "show_tool_indicators": True, "no_code_dump": True},
    "storage": {"max_mb": 500, "cleanup_days": 30, "auto_clean_startup": True},
    "sandbox": {"docker": False},
}
