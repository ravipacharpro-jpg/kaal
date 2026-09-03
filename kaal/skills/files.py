"""Files skill — safe ops, traversal block, size limits. Delete pe ask_cb.
Write/edit se pehle auto-backup (undo ke liye)."""
import os, time

MAX_READ_MB = 5
BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "memory", "backups"))

def _roots():
    """Safe roots: repo root + CWD + HOME. Kisi ek ke andar = safe.
    (Pehle sirf HOME tha — repo HOME ke bahar ho to legit files reject hoti thin.)"""
    roots = set()
    try:
        roots.add(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    except Exception:
        pass
    try:
        roots.add(os.path.abspath(os.getcwd()))
    except Exception:
        pass
    try:
        roots.add(os.path.abspath(os.path.expanduser("~")))
    except Exception:
        pass
    return roots

def _safe(path):
    p = os.path.abspath(os.path.expanduser(path))
    for r in _roots():
        try:
            if os.path.commonpath([p, r]) == r:
                return p
        except ValueError:
            pass
    return None

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

def _cp_dir():
    d = os.path.join(BACKUP_DIR, "checkpoints")
    os.makedirs(d, exist_ok=True)
    return d

def _touch(p):
    """Path ko tracked list me dalo (checkpoint iska fresh backup lega)."""
    import json
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(_index_path(), encoding="utf-8") as f:
            idx = json.load(f)
    except Exception:
        idx = {}
    if p not in idx:
        idx[p] = idx.get(p, "")
        try:
            with open(_index_path(), "w", encoding="utf-8") as f:
                json.dump(idx, f)
        except OSError:
            pass

def checkpoint(tag="auto"):
    """Claude-style checkpoint: tracked files ka FRESH backup + snapshot. Returns id."""
    import json
    try:
        with open(_index_path(), encoding="utf-8") as f:
            idx = json.load(f)
    except Exception:
        idx = {}
    for p in list(idx):
        bp = idx[p]
        if os.path.isfile(p):
            nb = _backup(p)  # current content ka fresh backup
            if nb:
                idx[p] = nb
        elif not (bp and os.path.isfile(bp)):
            del idx[p]  # file bhi gayi, backup bhi — stale entry hatao
    try:
        with open(_index_path(), "w", encoding="utf-8") as f:
            json.dump(idx, f)
    except Exception:
        pass
    cid = f"{int(time.time())}-{tag}"
    with open(os.path.join(_cp_dir(), cid + ".json"), "w", encoding="utf-8") as f:
        json.dump(idx, f)
    cps = sorted(os.listdir(_cp_dir()))
    for old in cps[:-10]:
        try: os.remove(os.path.join(_cp_dir(), old))
        except OSError: pass
    return f"Checkpoint: {cid} ({len(idx)} files tracked)"

def _restore_idx(idx):
    ok, skip = 0, 0
    for p, bp in idx.items():
        if not (bp and os.path.isfile(bp)):
            skip += 1
            continue
        try:
            with open(bp, "rb") as f:
                data = f.read(2000000)
            with open(p, "wb") as f:
                f.write(data)
            ok += 1
        except OSError:
            skip += 1
    return ok, skip

def rewind():
    """Last checkpoint pe wapas. Pehle current state auto-save (redo = dobara rewind)."""
    import json
    try:
        cps = sorted(os.listdir(_cp_dir()))
    except OSError:
        return "Koi checkpoint nahi"
    if not cps:
        return "Koi checkpoint nahi"
    try:
        with open(_index_path(), encoding="utf-8") as f:
            cur = json.load(f)
    except Exception:
        cur = {}
    with open(os.path.join(_cp_dir(), f"{int(time.time())}-pre-rewind.json"), "w", encoding="utf-8") as f:
        json.dump(cur, f)
    with open(os.path.join(_cp_dir(), cps[-1]), encoding="utf-8") as f:
        idx = json.load(f)
    ok, skip = _restore_idx(idx)
    try:
        with open(_index_path(), "w", encoding="utf-8") as f:
            json.dump(idx, f)
    except OSError:
        pass
    return f"Rewind: {ok} files wapas, {skip} skip (redo ke liye dobara /rewind)"

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
    _touch(p)
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

def _fuzzy_span(src, old):
    """Whitespace-normalized match. Returns (start, end) ya None."""
    import difflib
    norm = lambda s: "\n".join(l.rstrip() for l in s.splitlines())
    nsrc, nold = norm(src), norm(old)
    i = nsrc.find(nold)
    if i == -1:
        return None
    # normalized offset ko original me map karo (line-based)
    slines, olines = src.splitlines(True), nold.splitlines()
    nlines = nsrc.splitlines()
    start_line = nsrc[:i].count("\n")
    orig_start = sum(len(l) for l in slines[:start_line])
    # old ke line-count jitni original lines lo
    span_lines = slines[start_line:start_line + max(1, len(olines))]
    sm = difflib.SequenceMatcher(None, "".join(span_lines).rstrip(), nold.rstrip())
    if sm.ratio() < 0.85:
        return None
    return orig_start, orig_start + sum(len(l) for l in span_lines)

def edit_file(path, old, new, ask_cb=None, fuzzy=True, replace_all=False):
    """Old text ko new se badlo (default pehli occurrence; all=True pe saari).
    Exact na mile to fuzzy match. Diff preview + approval. Python syntax validate. Verify."""
    import difflib
    p = _safe(path)
    if not p or not os.path.isfile(p):
        return "File nahi mili ya path unsafe hai"
    with open(p, encoding="utf-8", errors="replace") as f:
        src = f.read()
    note = ""
    if old not in src:
        if not fuzzy:
            return "Old text file me mila nahi — pehle file_read karo"
        span = _fuzzy_span(src, old)
        if not span:
            return "Old text (fuzzy bhi) nahi mila — file_read/file_outline karo"
        old = src[span[0]:span[1]]
        note = "(fuzzy match) "
    new_src = src.replace(old, new) if replace_all else src.replace(old, new, 1)
    if p.endswith(".py"):
        import ast
        try:
            ast.parse(new_src)
        except SyntaxError as e:
            return f"Syntax toot jayegi — edit roki: {e}"
    diff = "".join(difflib.unified_diff(src.splitlines(True), new_src.splitlines(True),
                                        "pehle", "ab", n=2))[:1200]
    if ask_cb and not ask_cb(f"Ye change karu {note}{p} me?\n{diff[:600]}"):
        return "Edit cancel — permission deny"
    _backup(p)
    _touch(p)
    with open(p, "w", encoding="utf-8") as f:
        f.write(new_src[:200000])
    with open(p, encoding="utf-8", errors="replace") as f:
        check = f.read()
    if new[:200] not in check and new.strip()[:100] not in check:
        return "Verify fail — change apply nahi hui, undo karo"
    return f"Edit ho gayi {note}: {p} (undo: file_undo, verified ✅)\nDiff:\n{diff[:500]}"
