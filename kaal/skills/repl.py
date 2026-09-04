"""Persistent Python REPL — Prime-style kernel ka chhota, honest version.
Turns ke beech variables/state _NS me zinda rehte hain (in-process).
Safety: code.audit() pehle (import/open/eval/dunder block) + restricted builtins.
OS boundary nahi — sensitive machine pe /perm tight rakho.
"""
import io
from contextlib import redirect_stdout

_NS = {}

_SAFE_BUILTINS = {
    "print": print, "len": len, "range": range, "str": str, "int": int,
    "float": float, "bool": bool, "list": list, "dict": dict, "set": set,
    "tuple": tuple, "sum": sum, "min": min, "max": max, "sorted": sorted,
    "enumerate": enumerate, "zip": zip, "abs": abs, "round": round,
    "repr": repr, "type": type, "isinstance": isinstance,
}

def run(code):
    """Code chalao, state rakho. Returns output ya error (truncate)."""
    from . import code as _code
    why = _code.audit(code[:4000])
    if why:
        return why + " — repl me allowed nahi"
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(compile(code[:4000], "<kaal-repl>", "exec"),
                 {"__builtins__": dict(_SAFE_BUILTINS)}, _NS)
    except Exception as e:
        return f"Error: {e}"[:300]
    out = buf.getvalue().strip()[:800]
    return out if out else f"OK (vars: {len(_NS)})"

def reset():
    _NS.clear()
    return "REPL state clear"

def vars_list():
    return sorted(_NS.keys())[:50]
