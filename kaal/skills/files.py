"""Files skill — safe ops, traversal block, size limits. Delete pe ask_cb."""
import os

MAX_READ_MB = 5
ALLOWED_EXTRA = set()

def _safe(path):
    p = os.path.abspath(os.path.expanduser(path))
    home = os.path.expanduser("~")
    if ".." in os.path.relpath(p, home).split(os.sep):
        return None
    return p

def read_file(path, max_chars=2000):
    p = _safe(path)
    if not p or not os.path.isfile(p):
        return "File nahi mili ya path unsafe hai"
    if os.path.getsize(p) > MAX_READ_MB * 1024 * 1024:
        return "File bahut badi hai, limit 5MB"
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read(max_chars)[:max_chars]

def write_file(path, content, ask_cb=None):
    p = _safe(path)
    if not p:
        return "Unsafe path — write block"
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content[:100000])
    return f"Write ho gayi: {p}"

def list_dir(path="."):
    p = _safe(path)
    if not p or not os.path.isdir(p):
        return "Folder nahi mila ya unsafe path"
    items = sorted(os.listdir(p))[:50]
    return f"{p} me {len(items)} cheez: " + ", ".join(items)[:400]

def delete_path(path, ask_cb=None):
    p = _safe(path)
    if not p or not os.path.exists(p):
        return "Path mili nahi"
    if ask_cb and not ask_cb(f"Delete karu: {p}?"):
        return "Delete cancel — permission deny"
    import shutil
    if os.path.isdir(p):
        shutil.rmtree(p)
    else:
        os.remove(p)
    return f"Delete ho gayi: {p}"
