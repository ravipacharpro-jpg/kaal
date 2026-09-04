"""Chinese-comments skill (/comment-zh).
Global rule: code/identifiers English-only; comments kisi bhi language me.
LLM se Chinese comments lagwao — code lines byte-identical verify karke hi likho.
"""
SKILL = {"name": "zhcomment", "desc": "Chinese code comments (code unchanged, verified)",
         "version": "0.1.0",
         "tools": [{"name": "comment_zh", "desc": "File me Chinese comments lagao (code same rehta hai)",
                    "params": "path", "fn": lambda a: comment_file(a.get("path", ""), a.get("_ask"))}],
         "commands": ["/comment-zh <file>"]}

SYSTEM_ADD = ("Chinese-comment mode: Add concise Simplified-Chinese comments "
              "explaining purpose, complex logic, params, edge cases. "
              "STRICT: do not change, add, remove, or rename ANY code. "
              "Output ONLY the full file content, no explanations.")

def strip_comments(src, ext="py"):
    """Code lines only (comment-stripped) — change-verify ke liye. Pure fn."""
    out = []
    for line in src.splitlines():
        s = line.strip()
        if ext == "py" and s.startswith("#"):
            continue
        if ext in ("js", "java", "cpp", "c") and s.startswith("//"):
            continue
        out.append(line)
    return "\n".join(out)

def verify_unchanged(before, after, ext="py"):
    """Comments ke alawa kuch badla? True = safe to write."""
    return strip_comments(before, ext) == strip_comments(after, ext)

def comment_file(path, ask_cb=None):
    """LLM se Chinese comments + verify + approval write. Returns summary str."""
    from . import files as _files
    from ..models.router import try_chat
    p = _files._safe(path)
    if not p or not __import__("os").path.isfile(p):
        return "File nahi mili ya path unsafe hai"
    with open(p, encoding="utf-8", errors="replace") as f:
        src = f.read()
    if len(src) > 20000:
        return "File badi hai (20k+) — chhota hissa do"
    _, txt = try_chat([
        {"role": "system", "content": SYSTEM_ADD},
        {"role": "user", "content": f"FILE: {path}\n```\n{src}\n```"}])
    if not txt:
        return "LLM nahi (key/Ollama chahiye) — /setup se key add karo"
    ext = p.rsplit(".", 1)[-1] if "." in p else "py"
    if not verify_unchanged(src, txt, ext):
        return "Code lines badal gayi — write ROKI (sirf comments allowed the)"
    if ask_cb and not ask_cb(f"Chinese comments likhu {p} me? (code same, verify OK)"):
        return "Cancel — permission deny"
    return _files.write_file(p, txt)
