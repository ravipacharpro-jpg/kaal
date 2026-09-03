"""Code skill — AST-verified sandbox + optional docker (PC) + subprocess fallback.
Substring blocklist nahi — real parse tree check (obfuscation-proof).
NOTE: ye OS-level boundary nahi hai; strong isolation chahiye to /sandbox on (docker, PC pe).
"""
import ast, subprocess, sys

TIMEOUT = 30
BAD_CALLS = {"eval", "exec", "open", "compile", "__import__", "input",
             "memoryview", "breakpoint", "exit", "quit", "help", "license"}
BAD_ATTRS = {"system", "popen", "spawn", "socket", "remove", "rmdir", "unlink",
             "chmod", "chown", "kill", "fork", "execl", "execv", "environ",
             "getenv", "putenv", "rmtree", "call", "check_output", "run"}

def audit(code):
    """Returns None agar safe, warna wajah string."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "Block: import allowed nahi"
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            return f"Block: {node.id}"
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in BAD_ATTRS:
                return f"Block: .{node.attr}"
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in BAD_CALLS:
                return f"Block: {f.id}()"
    return None

def run_python(code, timeout=TIMEOUT):
    why = audit(code[:4000])
    if why:
        return why + " — sandbox me allowed nahi"
    try:
        from . import sandbox as _sb
        if _sb.enabled() and _sb.available():
            return "[docker] " + _sb.run_docker(code, timeout)
    except Exception:
        pass
    try:
        r = subprocess.run([sys.executable, "-c", code[:4000]],
                           capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr).strip()[:800]
        return out if out else f"Exit {r.returncode}, output khaali"
    except subprocess.TimeoutExpired:
        return f"Timeout {timeout}s — code bahut lamba chala"
    except Exception as e:
        return f"Error: {e}"[:200]
