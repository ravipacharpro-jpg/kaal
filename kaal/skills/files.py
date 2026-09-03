"""Files skill — safe ops, traversal block, size limits. Delete pe ask_cb.
Write/edit se pehle auto-backup (undo ke liye)."""
import os, time

MAX_READ_MB = 5
BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "memory", "backups"))

def _safe(path):
    p = os.path.abspath(os.path.expanduser(path))
    home = os.path.expanduser("~")
    if ".." in os.path.relpath(p, home).split(os.sep):
        return None
    return p

def read_file(path, max_chars=2000, offset=0, lines=0):
    """File padho. Badi file ke liye offset/lines se chunk me padho.
    read_file(path) pehle 2000 chars; aage ke liye offset badhao."""
    p = _safe(path)
    if not p or not os.path.isfile(p):
        return "File nahi mili ya path unsafe hai"
    if os.path.getsize(p) > MAX_READ_MB * 1024 * 1024:
        return "File bahut badi hai, limit 5MB"
    with open(p, encoding="utf-8", errors="replace") as f:
        content = f.read()
    total = len(content)
    if lines:
        parts = content.splitlines()
        chunk = "\n".join(parts[offset:offset + lines])
        more = f" [lines {offset}-{offset+lines}/{len(parts)}]" if offset + lines < len(parts) else " [end]"
        return chunk[:max_chars] + more
    chunk = content[offset:offset + max_chars]
    more = f" [chars {offset}-{offset+max_chars}/{total}]" if offset + max_chars < total else " [end]"
    return chunk + more

def outline(path):
    """Badi file ka naksha: functions/classes/headings list (Claude-style context)."""
    import re
    p = _safe(path)
    if not p or not os.path.isfile(p):
        return "File nahi mili ya path unsafe hai"
    with open(p, encoding="utf-8", errors="replace") as f:
        lines = f.read(500000).splitlines()
    pats = (r"^\s*(def|class|async def)\s+(\w+)", r"^\s*function\s+(\w+)",
            r"^#{1,3}\s+(.+)", r"^\s*(const|let|var|fn)\s+(\w+)")
    out = []
    for i, ln in enumerate(lines, 1):
        for pat in pats:
            m = re.match(pat, ln)
            if m:
                out.append(f"L{i}: {m.group(0).strip()[:70]}")
                break
        if len(out) >= 60:
            break
    head = f"{p}: {len(lines)} lines"
    return head + "\n" + ("\n".join(out) if out else "(koi structure nahi mili)")

def _index_path():
    return os.path.join(BACKUP_DIR, "index.json")

def _backup(p):
    """Original ka timestamped backup + index. Returns backup path ya ''."""
    import json
    try:
        if not os.path.isfile(p):
            return ""
        os.makedirs(BACKUP_DIR, exist_ok=True)
        bp = os.path.join(BACKUP_DIR, os.path.basename(p) + f".{int(time.time())}.bak")
        with open(p, "rb") as f, open(bp, "wb") as b:
            b.write(f.read(2000000))
        try:
            with open(_index_path(), encoding="utf-8") as f:
                idx = json.load(f)
        except Exception:
            idx = {}
        idx[p] = bp
        with open(_index_path(), "w", encoding="utf-8") as f:
            json.dump(idx, f)
        baks = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith(".bak"))
        for old in baks[:-20]:
            try: os.remove(os.path.join(BACKUP_DIR, old))
            except OSError: pass
        return bp
    except OSError:
        return ""

def undo_last(filename=""):
    """Last change wapas lao. filename ho to uska, warna sabse recent."""
    import json
    try:
        with open(_index_path(), encoding="utf-8") as f:
            idx = json.load(f)
    except Exception:
        return "Koi backup nahi — undo khaali"
    if not idx:
        return "Koi backup nahi — undo khaali"
    if filename:
        p = _safe(filename)
        bp = idx.get(p or "")
        if not bp:
            return "Is file ka koi backup nahi"
    else:
        p, bp = max(idx.items(), key=lambda kv: os.path.getmtime(kv[1]) if os.path.exists(kv[1]) else 0)
    try:
        with open(bp, "rb") as f:
            data = f.read(2000000)
        with open(p, "wb") as f:
            f.write(data)
        return f"Undo ho gaya: {p} wapas"
    except OSError as e:
        return f"Undo fail: {e}"[:150]

def write_file(path, content, ask_cb=None):
    p = _safe(path)
    if not p:
        return "Unsafe path — write block"
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    _backup(p)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content[:100000])
    return f"Write ho gayi: {p} (undo: file_undo)"

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
        return f"Delete ho gayi: {p} (folder — undo nahi)"
    _backup(p)
    os.remove(p)
    return f"Delete ho gayi: {p} (undo: file_undo)"

def edit_file(path, old, new, ask_cb=None):
    """Old text ko new se badlo. Pehle unified diff preview + approval. Summary return."""
    import difflib
    p = _safe(path)
    if not p or not os.path.isfile(p):
        return "File nahi mili ya path unsafe hai"
    with open(p, encoding="utf-8", errors="replace") as f:
        src = f.read()
    if old not in src:
        return "Old text file me mila nahi — pehle file_read karo"
    new_src = src.replace(old, new, 1)
    diff = "".join(difflib.unified_diff(src.splitlines(True), new_src.splitlines(True),
                                        "pehle", "ab", n=2))[:1200]
    if ask_cb and not ask_cb(f"Ye change karu {p} me?\n{diff[:600]}"):
        return "Edit cancel — permission deny"
    _backup(p)
    with open(p, "w", encoding="utf-8") as f:
        f.write(new_src[:200000])
    return f"Edit ho gayi: {p} (undo: file_undo)\nDiff:\n{diff[:500]}"
