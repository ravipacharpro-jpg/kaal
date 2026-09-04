"""Command Palette (Ctrl+P) — fuzzy slash-command picker, stdlib only.
POSIX: termios/tty raw single-keypress. Windows: msvcrt. Fallback: numbered list.
Nested palette: entry me 'options' ho to doosra level khulta hai.
/palette command se bhi khulta hai; Ctrl+P (\\x10) main_loop pakadta hai.
"""
import os

COMMANDS = [
    ("/bg <task>", "background + live-todo + interject", None),
    ("/plan <task>", "numbered plan likho", None),
    ("/approve", "pending plan approve + execute", None),
    ("/review <file>", "outline + syntax + checklist review", None),
    ("/research <query>", "explorer read-only research", None),
    ("/fresh <ticket>", "branch + 5-phase cycle", None),
    ("/ship [msg]", "secret-scan commit + push", None),
    ("/autopilot", "due jobs (max 3)", None),
    ("/model", "default/architect/editor model", ["auto", "1", "2", "3"]),
    ("/effort", "reasoning depth", ["low", "medium", "high"]),
    ("/perm", "permissions matrix", ["delete_files", "code_execution", "browser", "secrets"]),
    ("/keys", "API keys add/list/revive", ["add", "list", "revive"]),
    ("/theme", "accent color", ["cyan", "green", "magenta", "yellow"]),
    ("/session", "past sessions list/resume", None),
    ("/setup", "onboarding: provider keys add + test", None),
    ("/agents", "specialist personas dekho", None),
    ("/endpoints", "20 targets + budget", None),
    ("/budget", "kharch summary", None),
    ("/memory", "SQLite sessions", None),
    ("/user", "USER.md add/list", ["add"]),
    ("/thread", "thread continuity", ["clear"]),
    ("/trace", "run history table", None),
    ("/tree", "run-wise execution tree", None),
    ("/ollama", "local models pull/list", None),
    ("/schedule", "roz auto-kaam", None),
    ("/sandbox", "docker on/off (PC)", ["on", "off"]),
    ("/checkpoint", "manual checkpoint", None),
    ("/rewind", "last checkpoint wapas", None),
    ("/export", "session markdown export", None),
    ("/recipe", "reusable workflows", None),
    ("/plugin", "plugins enable/disable", None),
    ("/voice", "mic input (Termux:API)", None),
    ("/cache", "prompt cache stats/clear", ["clear"]),
    ("/comment-zh <file>", "Chinese comments (code same)", None),
    ("/reflect", "past reflections dekho", None),
    ("/quit", "band karo", None),
]

def fuzzy_match(query, text):
    """Subsequence fuzzy: saare query chars order me hon. Returns score ya None."""
    q, t = query.lower().strip(), text.lower()
    if not q:
        return 0
    it = iter(range(len(t)))
    pos = []
    for ch in q:
        for i in it:
            if t[i] == ch:
                pos.append(i)
                break
        else:
            return None
    span = pos[-1] - pos[0] + 1 if pos else 0
    start_bonus = 10 if t.startswith(q[:1]) else 0
    return start_bonus - span - len(t) // 50

def filter_commands(query):
    """(score, cmd, desc, options) sorted best-first. Pure — testable."""
    out = []
    for cmd, desc, opts in COMMANDS:
        s = fuzzy_match(query, cmd + " " + desc)
        if s is not None:
            out.append((s, cmd, desc, opts))
    out.sort(key=lambda r: (-r[0], r[1]))
    return [(c, d, o) for _, c, d, o in out]

def _read_key():
    """Single keypress (echo off). Returns str: char ya 'UP'/'DOWN'/'ENTER'/'ESC'."""
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"H": "UP", "P": "DOWN"}.get(ch2, "")
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == "\x1b":
            return "ESC"
        if ch == "\x7f":
            return "BACK"
        return ch
    import sys
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            import select
            if select.select([sys.stdin], [], [], 0.15)[0]:
                seq = sys.stdin.read(2)
                if seq == "[A":
                    return "UP"
                if seq == "[B":
                    return "DOWN"
                return "ESC"
            return "ESC"
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == "\x7f":
            return "BACK"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def pick(options, title="Palette", prompt="type to filter"):
    """Interactive fuzzy picker. Returns selected str ya ''.
    Non-TTY (pipe/CI) me numbered fallback."""
    import sys
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    if not sys.stdin.isatty():
        console.print(f"[dim]{title} (non-TTY — number likho):[/]")
        for i, o in enumerate(options[:20], 1):
            label = o[0] if isinstance(o, tuple) else o
            console.print(f"  {i}. {label}")
        try:
            n = int(console.input("[dim]# [/]").strip() or "0")
            o = options[n - 1]
            return o[0] if isinstance(o, tuple) else o
        except Exception:
            return ""
    query, idx = "", 0
    while True:
        shown = options if not query else None
        if query:
            scored = []
            for o in options:
                label = (o[0] if isinstance(o, tuple) else o)
                s = fuzzy_match(query, label)
                if s is not None:
                    scored.append((s, o))
            scored.sort(key=lambda r: (-r[0], str(r[1])))
            shown = [o for _, o in scored]
        idx = max(0, min(idx, max(0, len(shown) - 1)))
        lines = []
        for i, o in enumerate(shown[:12]):
            label = o[0] if isinstance(o, tuple) else o
            desc = o[1] if isinstance(o, tuple) and len(o) > 1 else ""
            mark = "→" if i == idx else " "
            lines.append(f"{mark} [bold]{label}[/]" + (f" [dim]— {desc}[/]" if desc else ""))
        console.clear()
        console.print(Panel("\n".join(lines) or "[dim]koi match nahi[/]",
                            title=f" {title} — {prompt}: {query}█",
                            border_style="cyan", padding=(0, 1)))
        console.print("[dim]↑↓ move · Enter select · Esc band[/]")
        try:
            k = _read_key()
        except Exception:
            return ""
        if k == "ESC" or k == "\x03":
            console.clear()
            return ""
        if k == "ENTER":
            console.clear()
            if not shown:
                return ""
            o = shown[idx]
            return o[0] if isinstance(o, tuple) else o
        if k == "UP":
            idx = (idx - 1) % max(1, len(shown))
        elif k == "DOWN":
            idx = (idx + 1) % max(1, len(shown))
        elif k == "BACK":
            query = query[:-1]
            idx = 0
        elif len(k) == 1 and k.isprintable():
            query += k
            idx = 0

def open_palette():
    """Full palette flow: command → (nested options) → final command string ya ''."""
    sel = pick([(c, d, o) for c, d, o in COMMANDS], title="Command Palette")
    if not sel:
        return ""
    for cmd, desc, opts in COMMANDS:
        if cmd == sel and opts:
            sub = pick(opts, title=cmd)
            if not sub:
                return ""
            base = cmd.split()[0]
            return f"{base} {sub}".strip()
    return sel
