"""Kaal premium Rich TUI — OpenCode style.
Clean monospace, single cyan accent, todo + live + summary.
Wide screen = side-by-side, Termux narrow = stacked.
"""
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.console import Console as _C

from ..agent import run_task
from ..agents.orchestrator import PERSONAS as AGENT_PERSONAS
from ..config_store import get_all as cfg_all, set_perm as cfg_set_perm
from ..memory.store import recent
from ..models.ollama import status_line
from ..models.ollama import PRESETS as OLLAMA_PRESETS, pull as ollama_pull, detect as ollama_detect
from ..models.router import add_user_key, budget_status, list_endpoints
from ..models.router import POPULAR_MODELS, get_model, set_model
from ..models.router import get_role_model, set_role_model
from ..models.router import get_effort, set_effort
from ..platform_adapt import describe as plat_describe
from ..scheduler import add as sched_add, due as sched_due
from ..storage import startup_check
from ..i18n import t as _t
from . import theme as th
from .brand import brand, agent_name

console = Console()


def ask_main(q):
    """TUI permission prompt (diff-aware color). /ship jaise commands ke liye."""
    return Confirm.ask(f"[bold yellow]{q[:300]}[/]")


def _run_bg(task):
    """Background task + live-todo panel + interject/cancel.
    Task ek thread me, stdin sirf main thread padhta hai (dual-reader mess nahi).
    Beech me kuch likho → note task ko; 'ruk jao'/'cancel' → clean stop."""
    import queue
    import threading
    import time as _t
    from ..agents.orchestrator import decompose as _deco
    try:
        jobs = _deco(task)
    except Exception:
        jobs = []
    todos = [{"title": j["step"][:45], "agent": j["agent"], "status": "pending"} for j in jobs] or [
        {"title": task[:45], "agent": "general", "status": "pending"}]
    shared = {"msg": "shuru...", "done": False, "result": None}
    inbox, cancel = queue.Queue(), threading.Event()

    def _step(title, status):
        for td in todos:
            if td["title"][:30] == (title or "")[:30]:
                td["status"] = status
                break
        else:
            todos.append({"title": (title or "")[:45], "agent": "brain", "status": status})
        shared["msg"] = f"{title[:60]} [{status}]"

    def _live(m):
        shared["msg"] = m

    def _work():
        try:
            shared["result"] = run_task(task, live_cb=_live, ask_cb=lambda q: False,
                                        step_cb=_step, cancel=cancel, inbox=inbox)
        except Exception as e:
            shared["result"] = {"status": "error", "summary": f"BG error: {e}"[:200],
                                "todos": todos, "endpoint": "-", "mode": "bg"}
        shared["done"] = True

    def _render():
        t = Table(show_header=False, border_style="dim", box=None)
        t.add_column(" ", style="dim")
        t.add_column("Step", style="bold")
        t.add_column("Agent", style="dim")
        glyph = {"pending": "○", "doing": "→", "done": "✓"}
        for td in todos[-12:]:
            st = td.get("status", "pending")
            t.add_row(glyph.get(st, "○"), td["title"][:45], td.get("agent", ""))
        g = Group(t, Text(shared["msg"][:90], style="dim"))
        return Panel(g, title=" BG task (likho = note, 'ruk jao' = cancel)",
                     border_style=th.ACCENT, padding=(0, 1))

    th_run = threading.Thread(target=_work, daemon=True)
    th_run.start()
    with Live(_render(), console=console, refresh_per_second=4) as live:
        while not shared["done"]:
            live.update(_render())
            try:
                line = Prompt.ask(f"[bold {th.ACCENT}]bg[/] [dim]›[/]").strip()
            except (EOFError, KeyboardInterrupt):
                cancel.set()
                break
            if shared["done"]:
                break
            low = line.lower()
            if low in ("ruk jao", "ruko", "cancel", "stop", "/cancel"):
                cancel.set()
                shared["msg"] = "rukne ka signal — wind-down..."
            elif line:
                inbox.put(line)
                shared["msg"] = f"note bheja: {line[:60]}"
    th_run.join(timeout=30)
    res = shared["result"] or {"status": "cancelled", "summary": "Task roka.",
                               "todos": todos, "endpoint": "-", "mode": "bg"}
    show_result(res)


def _status_strip():
    parts = []
    try:
        b = budget_status()
        parts.append(f"[dim]{b['used']}/{b['budget']}[/] · {b['mode']}")
    except Exception:
        pass
    try:
        eps = list_endpoints()
        parts.append(f"[dim]{len(eps)} endpoints[/]")
    except Exception:
        pass
    try:
        parts.append(f"[dim]{get_model()}[/] · [dim]{get_effort()}[/]")
    except Exception:
        pass
    try:
        parts.append(f"[dim]{plat_describe().replace(' ', '')}[/]")
    except Exception:
        pass
    return " · ".join(parts)


def show_header():
    """Nexus-style landing: fresh screen, centered brand, input box visual,
    model line, hints, bottom version bar. Narrow screens stack safely."""
    from rich.align import Align as _Align
    try:
        console.clear()
    except Exception:
        pass
    console.print()
    console.print(_Align.center(brand()))
    try:
        from .brand import VERSION as _V
    except Exception:
        _V = ""
    try:
        _model_line = f"{get_model()} · {get_effort()}"
    except Exception:
        _model_line = "auto · medium"
    try:
        _b = budget_status()
        _pct = f"{_b.get('pct', 0)}%"
    except Exception:
        _pct = "–"
    _box_w = min(72, max(40, console.width - 8))
    _ask = Panel(Text("Ask anything...  (seedha task likho)", style="dim"),
                 border_style=th.ACCENT, width=_box_w, padding=(0, 2))
    console.print(_Align.center(_ask))
    console.print(_Align.center(
        f"[magenta]kaal[/] [dim]·[/] {_model_line} [dim]·[/] [yellow]{_pct}[/]"))
    console.print(_Align.center("[dim]/agents  ctrl+p commands  /dashboard[/]"))
    console.print(f"[dim]{_status_strip()}[/]")
    console.print(Rule(style="dim"))
    console.print(_Align.right(f"[dim]~  KAAL {_V}[/]"))
    console.print(th.FOOTER_HINT + "\n")


def dashboard_data():
    """Dashboard ke liye data dict (pure-ish, testable)."""
    from ..models.router import session_used, session_cap, get_effort
    from ..models.router import get_model, key_health
    from ..skills import promptcache as _pcd
    from ..platform_adapt import detect as _pdet
    d = {"platform": "?", "model": "?", "effort": "?", "budget": "?",
         "session": "?", "cache": "?", "keys": {}, "sessions": []}
    try:
        d["platform"] = _pdet()
    except Exception:
        pass
    try:
        d["model"] = get_model()
        d["effort"] = get_effort()
    except Exception:
        pass
    try:
        b = budget_status()
        d["budget"] = f"{b['used']}/{b['budget']} ({b['pct']}%)"
    except Exception:
        pass
    try:
        d["session"] = f"{session_used()}/{session_cap()}"
    except Exception:
        pass
    try:
        n, s = _pcd.stats()
        d["cache"] = f"{n} entries, ~{s} saved"
    except Exception:
        pass
    try:
        d["keys"] = {p: len(r) for p, r in key_health().items()}
    except Exception:
        pass
    try:
        d["sessions"] = [(t[:40], s[:60]) for t, s in recent(5)]
    except Exception:
        pass
    return d


def show_dashboard():
    """OpenCode-style overview: status | sessions | keys (side-by-side)."""
    d = dashboard_data()
    t1 = Table(show_header=False, border_style="dim", box=None, pad_edge=False)
    t1.add_column("K", style="dim")
    t1.add_column("V", style="bold")
    for k in ("platform", "model", "effort", "budget", "session", "cache"):
        t1.add_row(k, str(d[k])[:40])
    p1 = Panel(t1, title=" Status", border_style=th.ACCENT, padding=(0, 1))
    if d["sessions"]:
        t2 = Table(show_header=False, border_style="dim", box=None, pad_edge=False)
        t2.add_column("Task", style="bold")
        for t, _s in d["sessions"]:
            t2.add_row(t[:44])
    else:
        t2 = Text("Khaali — pehla task karo.", style="dim")
    p2 = Panel(t2, title=" Sessions", border_style="dim", padding=(0, 1))
    if d["keys"]:
        t3 = Table(show_header=False, border_style="dim", box=None, pad_edge=False)
        t3.add_column("Provider", style="bold")
        t3.add_column("Keys", justify="right")
        for p, n in d["keys"].items():
            t3.add_row(p, str(n))
    else:
        t3 = Text("No keys — /setup karo.", style="dim")
    p3 = Panel(t3, title=" Keys", border_style="dim", padding=(0, 1))
    if console.width >= 100:
        console.print(Columns([p1, p2, p3], equal=True, expand=True))
    else:
        console.print(p1)
        console.print(p2)
        console.print(p3)


def show_endpoints():
    t = Table(title=" Endpoints", show_header=True,
              header_style=f"bold {th.ACCENT}", border_style="dim",
              show_lines=False)
    t.add_column("#", style="dim", width=3)
    t.add_column("Endpoint", style="bold")
    t.add_column("Limit", justify="right")
    t.add_column("Desc", style="dim")
    for i, e in enumerate(list_endpoints(), 1):
        lim = "∞" if e["daily_limit"] == -1 else str(e["daily_limit"])
        mark = " " if i == 1 else " "
        t.add_row(str(i), mark + e["name"], lim, e["desc"][:44])
    console.print(Panel(t, border_style="dim", padding=(0, 1)))
    console.print(f"[dim]{status_line()}[/]")


def show_todos(todos):
    t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
              border_style="dim", box=None, pad_edge=False, show_lines=False)
    t.add_column("", width=2)
    t.add_column("Kaam", style="bold")
    t.add_column("Agent", style=DIM)
    t.add_column("Status", justify="right")
    icon = {"pending": "[dim]·[/]", "doing": "[yellow]→[/]", "done": "[green]✔[/]"}
    for td in todos:
        t.add_row(icon.get(td["status"], "?"), td["title"][:46],
                  td.get("agent", "-")[:14], td["status"])
    return Panel(t, title="[bold]" + _t('tasks_title') + "[/]", border_style="dim", padding=(0, 1))


def show_result(res):
    wide = console.width >= 100
    footer = (f"via {res['endpoint']} · {res.get('mode', 'single')} · "
              f"{res.get('budget', '')} · memory saved")
    try:
        from ..models.router import session_used as _su, session_cap as _sc
        from ..skills import promptcache as _pce
        _n, _s = _pce.stats()
        footer += f" · session {_su()}/{_sc()} · cache {_n}/{_s}"
    except Exception:
        pass
    body = Group(Markdown(res["summary"][:600]), Text(footer, style=DIM))
    result = Panel(body, title="[bold green]" + _t('result_title') + "[/]",
                    border_style="dim", padding=(1, 2))
    todos = show_todos(res["todos"])
    if wide:
        console.print(Columns([todos, result], equal=True, expand=True))
    else:
        console.print(todos)
        console.print(result)
    try:
        from ..models.router import pop_notices
        for _n in pop_notices():
            console.print(f"[bold yellow]{_n[:200]}[/]")
    except Exception:
        pass
    console.print(Rule(style="dim"))


def show_budget():
    b = budget_status()
    pct = b["pct"]
    bar = "" * (pct // 10) + "" * (10 - pct // 10)
    console.print(Panel(
        f"[bold]{bar}[/]  {b['used']}/{b['budget']} tokens ({pct}%)\n"
        f" policy: [bold]{b['mode']}[/]",
        title=_t('budget_title'), border_style=th.WARN, padding=(1, 2)))


def show_memory():
    rows = recent(5)
    if not rows:
        console.print(f"[dim]{_t('memory_empty')}[/]")
        return
    t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
              border_style="dim", box=None)
    t.add_column("Task", style="bold")
    t.add_column("Summary", style="dim")
    for task, summ in rows:
        t.add_row(task[:44], summ[:64])
    console.print(Panel(t, title=" Memory", border_style=th.ACCENT, padding=(0, 1)))


def show_agents():
    t = Table(show_header=False, border_style="dim", box=None)
    t.add_column("Agent", style="bold magenta")
    t.add_column("Persona", style="dim")
    for a, role in AGENT_PERSONAS.items():
        if a == "general":
            continue
        t.add_row(" " + a, role[:70])
    console.print(Panel(t, title=" Agents", border_style="magenta", padding=(0, 2)))


def _run_with_live(task):
    from ..models.router import estimate
    try:
        console.print(f"[dim] Cost estimate: {estimate(task)}[/]")
    except Exception:
        pass
    try:
        from ..agents.orchestrator import decompose
        jobs = decompose(task)
        if len(jobs) > 1:
            t = Table(show_header=False, border_style="dim", box=None)
            t.add_column(" ", style="dim")
            t.add_column("Step", style="bold")
            t.add_column("Agent", style="dim")
            for j in jobs:
                t.add_row("○", j["step"][:50], j["agent"])
            console.print(Panel(t, title=" Plan (live states neeche summary me)",
                                border_style="dim", padding=(0, 1)))
    except Exception:
        pass
    live = {"msg": "soch raha hu..."}
    with Progress(SpinnerColumn(style=th.ACCENT),
                   TextColumn(" {task.fields[live]}"),
                   BarColumn(bar_width=None),
                   TextColumn("{task.percentage:.0f}%"),
                   console=console, transient=True) as prog:
        pt = prog.add_task("live", total=100, live=live["msg"])

        def wrap(m):
            live["msg"] = m
            done = min(95, prog.tasks[0].completed + 7)
            prog.update(pt, live=m, completed=done)

        def stream_wrap(piece):
            tail = piece.replace("\n", " ")[-60:]
            live["msg"] = f" {tail}"
            prog.update(pt, live=live["msg"])

        def ask_colored(q):
            from rich.text import Text
            if "\n+" in q or "\n-" in q or q.strip().startswith(("+++", "---", "@@")) or "Diff:" in q:
                t = Text()
                for line in q.splitlines():
                    if line.startswith("+") and not line.startswith("+++"):
                        t.append(line + "\n", style="green")
                    elif line.startswith("-") and not line.startswith("---"):
                        t.append(line + "\n", style="red")
                    elif line.startswith("@@"):
                        t.append(line + "\n", style="cyan")
                    else:
                        t.append(line + "\n")
                console.print(Panel(t, title="[bold yellow] Approval[/]", border_style="yellow",
                                    padding=(0, 1)))
                return Confirm.ask("[bold yellow]Aage badhu?[/]")
            return Confirm.ask(f"[bold yellow]  {q}[/]")

        res = run_task(task, live_cb=wrap,
                       ask_cb=ask_colored,
                       on_token=stream_wrap,
                       ask_text_cb=lambda q: Prompt.ask(f"[bold yellow] {q}[/]"))
        prog.update(pt, completed=100)
    return res


def main_loop():
    try:
        th.load_accent()
    except Exception:
        pass
    show_header()
    while True:
        try:
            task = Prompt.ask(f"[bold {th.ACCENT}]{agent_name()}[/] [dim]›[/]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print(f"\n[yellow]{_t('quit_bye')}[/]")
            break
        if not task:
            continue
        if task in ("/quit", "/q", "quit"):
            console.print(f"[yellow]{_t('quit_short')}[/]")
            break
        if task in ("\x10", "/palette"):
            # Ctrl+P (raw \x10 char) ya /palette — fuzzy command picker
            from . import palette as _pal
            sel = _pal.open_palette()
            if not sel:
                continue
            import re as _re
            if "<" in sel and ">" in sel:
                base = sel.split("<")[0].strip()
                try:
                    arg = Prompt.ask(f"[dim]{base} arg[/]").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if not arg:
                    continue
                task = f"{base} {arg}"
            else:
                task = sel
            if task.startswith("/"):
                pass  # neeche command dispatch me jayega
            else:
                res = _run_with_live(task)
                show_result(res)
                continue
        if task == "/endpoints":
            show_endpoints()
            continue
        if task == "/dashboard":
            show_dashboard()
            continue
        if task.startswith("/lang"):
            from ..i18n import set_lang, get_lang, LANGS
            parts = task.split()
            if len(parts) < 2:
                console.print(f"[dim]Language: {get_lang()} ({'/'.join(LANGS)})[/]")
                console.print(f"[dim]{_t('lang_use')}[/]")
                continue
            console.print(f"[green]{set_lang(parts[1])}[/]")
            continue
        if task == "/platform":
            from ..platform_adapt import capabilities as _caps
            caps = _caps()
            t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
                      border_style="dim", box=None)
            t.add_column("Capability", style="bold")
            t.add_column("Status", justify="right")
            for k in ("docker", "lsp_server", "daemon_service", "big_index",
                      "voice_mic", "parallel", "note"):
                v = caps.get(k, "?")
                mark = "[green]on[/]" if v is True else ("[red]off[/]" if v is False
                                                        else f"[yellow]{v}[/]")
                t.add_row(k, mark)
            probes = ", ".join(f"{k}={'✓' if v else '✗'}" for k, v in caps["probes"].items())
            console.print(Panel(t, title=f" Platform: {caps['platform']}",
                                border_style=th.ACCENT, padding=(0, 1)))
            console.print(f"[dim]probes: {probes}[/]")
            continue
        if task == "/theme":
            from . import theme as _thm
            console.print(f"[dim]Accent: {_thm.ACCENT} — use: /theme cyan|green|magenta|yellow[/]")
            continue
        if task.startswith("/theme"):
            from . import theme as _thm2
            import json as _js2
            name = task.split()[1].lower() if len(task.split()) > 1 else ""
            if name not in ("cyan", "green", "magenta", "yellow", "red", "blue"):
                console.print("[dim]Use: /theme cyan|green|magenta|yellow|red|blue[/]")
                continue
            _thm2.ACCENT = name
            try:
                import os as _os2
                tp = _os2.path.abspath(_os2.path.join(
                    _os2.path.dirname(__file__), "..", "..", "config", "tui.json"))
                d = {}
                try:
                    with open(tp, encoding="utf-8") as _f:
                        d = _js2.load(_f)
                except Exception:
                    pass
                d["accent"] = name
                _os2.makedirs(_os2.path.dirname(tp), exist_ok=True)
                with open(tp, "w", encoding="utf-8") as _f:
                    _js2.dump(d, _f, indent=2)
            except Exception:
                pass
            console.print(f"[green]Theme accent: {name} (tui.json me saved)[/]")
            continue
        if task == "/session":
            from ..memory.store import recent as _sr
            rows = _sr(10)
            if not rows:
                console.print(f"[dim]{_t('no_sessions')}[/]")
                continue
            for i, (t, _s) in enumerate(rows, 1):
                console.print(f"  {i}. {t[:60]}")
            console.print("[dim]Use: /session <n> — nth resume[/]")
            continue
        if task.startswith("/session"):
            from ..memory.store import recent as _sr2
            parts = task.split()
            try:
                n = int(parts[1]) - 1
                rows = _sr2(10)
                if 0 <= n < len(rows):
                    console.print(f"↩ Resume: {rows[n][0][:80]}")
                    res = _run_with_live(rows[n][0])
                    show_result(res)
                    continue
            except Exception:
                pass
            console.print("[dim]Use: /session <n>[/]")
            continue
        if task == "/setup" or task.startswith("/setup"):
            from . import setup as _su
            _su.run_setup()
            continue
        if task == "/budget":
            show_budget()
            continue
        if task == "/memory":
            show_memory()
            continue
        if task.startswith("/user"):
            from ..memory.persona import read_all as _who, ensure as _who_ensure
            import os as _os
            parts = task.split(" ", 2)
            if len(parts) >= 3 and parts[1] == "add":
                _who_ensure()
                p = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "memory", "USER.md"))
                with open(p, "a", encoding="utf-8") as _f:
                    _f.write(f"\n- {parts[2][:200]}\n")
                console.print("[green]USER.md me likh diya.[/]")
                continue
            console.print(Panel(_who() or "[dim]Khaali.[/]", title=" USER + MEMORY",
                                border_style=th.ACCENT, padding=(0, 1)))
            console.print("[dim]Use: /user add <baat> — ya memory/USER.md seedha edit karo[/]")
            continue
        if task == "/agents":
            show_agents()
            continue
        if task.startswith("/key"):
            parts = task.split()
            if len(parts) < 3:
                console.print("[dim]Use: /key openai sk-... "
                              "(openai groq openrouter together mistral gemini xai)[/]")
                continue
            console.print(f"[green]{add_user_key(parts[1], parts[2])}[/]")
            continue
        if task.startswith("/schedule"):
            from ..scheduler import list_jobs, remove as _rm
            parts = task.split(" ", 2)
            if len(parts) == 1 or parts[1] == "ls":
                jobs = list_jobs()
                if not jobs:
                    console.print("[dim]Koi job nahi. /schedule add 86400 task[/]")
                    continue
                t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
                          border_style="dim", box=None)
                t.add_column("#", style="dim"); t.add_column("Task", style="bold"); t.add_column("Har", justify="right")
                for i, j in enumerate(jobs):
                    t.add_row(str(i), j["task"][:50], f"{j.get('interval', 86400)}s")
                console.print(Panel(t, title="⏰ Jobs", border_style=th.ACCENT, padding=(0, 1)))
                continue
            if parts[1] == "rm" and len(parts) > 2:
                console.print(f"[yellow]{_rm(parts[2].strip())}[/]")
                continue
            if parts[1] == "log":
                from ..scheduler import log_tail
                lines = log_tail()
                console.print(Panel("".join(lines) or "[dim]Koi run log nahi.[/]",
                                    title=" Schedule log", border_style="dim"))
                continue
            if parts[1] == "add" and len(parts) > 2:
                rest = parts[2].split(" ", 1)
                if len(rest) < 2 or not rest[0].isdigit():
                    console.print("[dim]Use: /schedule add 86400 task yahan[/]")
                    continue
                console.print(f"[green]{sched_add(rest[1], int(rest[0]))}[/]")
                continue
            if parts[1].isdigit() and len(parts) > 2:
                console.print(f"[green]{sched_add(parts[2], int(parts[1]))}[/]")
                continue
            jobs = sched_due()
            console.print(f"[dim]Due jobs: {len(jobs)}[/]")
            for j in jobs[:5]:
                console.print(f"⏰ {j['task'][:60]}")
            console.print("[dim]Use: /schedule add 86400 task | /schedule ls | /schedule rm N | /schedule log[/]")
            continue
        if task.startswith("/logs"):
            from .. import log as _lg
            parts = task.split()
            try:
                n = max(1, min(int(parts[1]), 200)) if len(parts) > 1 else 30
            except Exception:
                n = 30
            lines = _lg.tail(n)
            if not lines:
                console.print("[dim]Log khaali hai — koi task/crash abhi tak nahi.[/]")
                continue
            console.print(Panel("".join(lines)[-3000:],
                                title=f" logs/kaal.log (akhri {len(lines)})",
                                border_style="dim", padding=(0, 1)))
            continue
        if task == "/trace":
            from ..trace import recent as _tr
            rows = _tr()
            if not rows:
                console.print("[dim]Koi trace nahi — pehla task chalao.[/]")
                continue
            t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
                      border_style="dim", box=None)
            t.add_column("Task", style="bold"); t.add_column("Mode"); t.add_column("EP", style="dim")
            t.add_column("Steps", justify="right"); t.add_column("Secs", justify="right"); t.add_column("Status", justify="right")
            for e in rows:
                st = "[green]done[/]" if e.get("status") == "done" else f"[yellow]{e.get('status')}[/]"
                t.add_row(e.get("task", "")[:36], e.get("mode", ""), e.get("endpoint", "")[:14],
                          str(e.get("steps", "")), str(e.get("secs", "")), st)
            console.print(Panel(t, title=" Trace (coze-loop lite)", border_style=th.ACCENT, padding=(0, 1)))
            continue
        if task.startswith("/perm"):
            parts = task.split()
            if len(parts) < 3:
                perms = cfg_all()["permissions"]
                t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
                          border_style="dim", box=None)
                t.add_column("Op", style="bold")
                t.add_column("Mode", justify="right")
                for k, v in perms.items():
                    if k != "note":
                        color = {"ask": "yellow", "allow": "green",
                                 "deny": "red"}.get(v, "dim")
                        t.add_row(k, f"[{color}]{v}[/]")
                console.print(Panel(t, title=" Permissions",
                                    border_style=th.ACCENT, padding=(0, 1)))
                console.print("[dim]Use: /perm delete_files allow|ask|deny[/]")
                console.print("[dim]Scoped: /perm delete_files:/tmp allow (longest-prefix match)[/]")
                continue
            console.print(f"[green]{cfg_set_perm(parts[1], parts[2])}[/]")
            continue
        if task.startswith("/plugin"):
            from ..skills.pluginman import list_all as _pl_list, enable as _pl_en
            parts = task.split()
            items = _pl_list()
            if len(parts) < 3:
                if not items:
                    console.print("[dim]Koi plugin nahi. skills/plugins/<name>.py me TOOLS rakho.[/]")
                else:
                    t = Table(show_header=False, border_style="dim", box=None)
                    t.add_column("Plugin", style="bold")
                    t.add_column("State", justify="right")
                    for n, on in items:
                        t.add_row(n, "[green]ON[/]" if on else "[dim]OFF[/]")
                    console.print(Panel(t, title=" Plugins", border_style=th.ACCENT))
                console.print("[dim]Use: /plugin enable name | /plugin disable name[/]")
                continue
            if parts[1] in ("enable", "disable") and len(parts) > 2:
                console.print(f"[green]{_pl_en(parts[2], parts[1] == 'enable')}[/]")
                console.print("[dim]Restart pe load hoga.[/]")
                continue
        if task == "/voice":
            import shutil, subprocess
            if shutil.which("termux-speech-to-text") is None:
                console.print("[dim]Voice ke liye Termux:API chahiye: pkg install termux-api. PC pe supported nahi.[/]")
                continue
            console.print("[dim] Bolo... (sun raha hu)[/]")
            try:
                r = subprocess.run(["termux-speech-to-text"], capture_output=True,
                                   text=True, timeout=30)
                heard = r.stdout.strip()[:300]
            except Exception as e:
                heard = ""
            if not heard:
                console.print("[dim]Kuch sunai nahi diya.[/]")
                continue
            console.print(f"[bold] Suna: {heard}[/]")
            res = _run_with_live(heard)
            show_result(res)
            continue
        if task.startswith("/sandbox"):
            from ..skills.sandbox import available as _sb_av
            parts = task.split()
            if len(parts) < 2:
                on = cfg_all().get("sandbox", {}).get("docker", False)
                console.print(f"[dim]Docker sandbox: {'ON' if on else 'OFF'} | docker mili: {'haan' if _sb_av() else 'nahi'}[/]")
                console.print("[dim]Use: /sandbox on|off (PC pe docker chahiye, Termux pe nahi chalega)[/]")
                continue
            cfg = cfg_all()
            cfg.setdefault("sandbox", {})["docker"] = parts[1].lower() == "on"
            import json as _js, os as _os
            _p = _os.path.join(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "config")), "sandbox.json")
            with open(_p, "w", encoding="utf-8") as _f:
                _js.dump({"docker": parts[1].lower() == "on"}, _f, indent=2)
            console.print(f"[green]Sandbox docker: {parts[1].lower()}[/]")
            continue
        if task == "/checkpoint":
            from ..skills.files import checkpoint as _cp
            console.print(f"[green]{_cp('manual')}[/]")
            continue
        if task == "/rewind":
            from ..skills.files import rewind as _rw
            if Confirm.ask("Last checkpoint pe rewind karu?"):
                console.print(f"[yellow]{_rw()}[/]")
            else:
                console.print("[dim]Rewind cancel.[/]")
            continue
        if task.startswith("/export"):
            from ..memory.store import export_md
            parts = task.split(" ", 1)
            console.print(f"[green]{export_md(parts[1].strip() if len(parts) > 1 else '')}[/]")
            continue
        if task.startswith("/thread"):
            from ..memory.patterns import thread_context
            parts = task.split()
            if len(parts) > 1 and parts[1] == "clear":
                import os as _os
                p = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "memory", "thread.json"))
                try:
                    _os.remove(p)
                except OSError:
                    pass
                console.print("[green]Thread clear — nayi shuruaat.[/]")
                continue
            th_ctx = thread_context()
            console.print(Panel(th_ctx or "[dim]Thread khaali.[/]", title=" Thread",
                                border_style=th.ACCENT, padding=(0, 1)))
            continue
        if task.startswith("/plan"):
            from ..planner import draft, write, read as plan_read
            what = task[5:].strip()
            if not what:
                cur = plan_read()
                console.print(Panel(cur or "[dim]Koi plan nahi. Use: /plan task yahan[/]",
                                    title=" PLAN.md", border_style=th.ACCENT))
                continue
            steps = draft(what)
            write(what, steps)
            t = Table(show_header=False, border_style="dim", box=None)
            t.add_column("#", style="dim"); t.add_column("Step", style="bold")
            for i, s in enumerate(steps, 1):
                t.add_row(str(i), s[:70])
            console.print(Panel(t, title=f" Plan: {what[:50]}", border_style=th.ACCENT))
            if Confirm.ask("Plan approve? (yes = execute)"):
                from ..agent import run_task as _rt
                res = _run_with_live(what)
                show_result(res)
            else:
                console.print("[dim]Plan PLAN.md me saved — /approve se chalao.[/]")
            continue
        if task == "/approve":
            from ..planner import read as plan_read
            cur = plan_read()
            if not cur:
                console.print("[dim]Koi plan nahi.[/]")
                continue
            first = cur.splitlines()[0].replace("# Plan:", "").strip()
            res = _run_with_live(first or "plan execute karo")
            show_result(res)
            continue
        if task.startswith("/recipe"):
            from ..recipes import list_all, get as recipe_get
            parts = task.split(" ", 1)
            if len(parts) < 2:
                console.print(Panel(" " + " | ".join(list_all() or ["koi nahi"]),
                                    title="Recipes", border_style=th.ACCENT))
                console.print("[dim]Use: /recipe morning-review[/]")
                continue
            steps = recipe_get(parts[1].strip())
            if not steps:
                console.print("[red]Recipe mili nahi.[/]")
                continue
            for s in steps:
                console.print(f"[dim] {s[:70]}[/]")
                res = _run_with_live(s)
                show_result(res)
            continue
        if task.startswith("/ollama"):
            parts = task.split(" ", 1)
            ok, models = ollama_detect()
            if len(parts) < 2:
                console.print(Panel(
                    (f"Models: {', '.join(models) if models else 'koi nahi'}\n" if ok else "") +
                    "Presets: " + ", ".join(OLLAMA_PRESETS),
                    title=f" Ollama ({'live ' if ok else 'band — `ollama serve` karo'})",
                    border_style=th.ACCENT, padding=(0, 1)))
                console.print("[dim]Use: /ollama nous-hermes2[/]")
                continue
            console.print(f"[green]{ollama_pull(parts[1].strip())}[/]")
            continue
        if task.startswith("/model"):
            parts = task.split()
            if len(parts) == 3 and parts[1] in ("architect", "editor"):
                name = parts[2].strip()
                pick = POPULAR_MODELS[int(name) - 1] if name.isdigit() and 1 <= int(name) <= len(POPULAR_MODELS) else name
                console.print(f"[green]{set_role_model(parts[1], pick)}[/]")
                continue
            if len(parts) < 2:
                console.print(f"[dim]Default: {get_model()} | architect: {get_role_model('architect')} | editor: {get_role_model('editor')}[/]")
                t = Table(show_header=False, border_style="dim", box=None)
                t.add_column("#", style="dim")
                t.add_column("Model", style="bold")
                for i, m in enumerate(POPULAR_MODELS, 1):
                    t.add_row(str(i), m)
                console.print(Panel(t, title=" Models (OpenRouter 75+ via openrouter key)",
                                    border_style=th.ACCENT, padding=(0, 1)))
                console.print("[dim]Use: /model 5 · /model architect 3 · /model editor 5[/]")
                continue
            name = parts[1].strip()
            pick = POPULAR_MODELS[int(name) - 1] if name.isdigit() and 1 <= int(name) <= len(POPULAR_MODELS) else name
            console.print(f"[green]{set_model(pick)}[/]")
            continue
        if task == "/keys":
            parts = task.split()
            if len(parts) >= 3 and parts[1] == "add":
                provider = parts[2].strip()
                key = parts[3].strip() if len(parts) > 3 else ""
                result = add_user_key(provider, key)
                console.print(f"[green]{result}[/]")
                continue
            if len(parts) >= 2 and parts[1] == "list":
                from ..models.router import key_health as _kh
                health = _kh()
                if not health:
                    console.print("[dim]No API keys configured yet. Use: /keys add <provider> <key>[/]")
                else:
                    glyph = {"active": "[green]✅[/]", "cooldown": "[yellow]⚠️[/]",
                             "dead": "[red]❌[/]"}
                    for prov, rows in health.items():
                        console.print(f"[bold]{prov}[/] ({len(rows)}):")
                        for r in rows:
                            console.print(f"  #{r['n']} {glyph.get(r['status'], '?')} "
                                          f"[dim]{r['masked']}[/] fails={r['fails']}")
                console.print("[dim]Providers: openai, anthropic, openrouter, groq, together, mistral, gemini, xai, deepseek, kimi, glm, tongyi, github[/]")
                console.print("[dim]Use: /keys revive <provider> <n>[/]")
                continue
            if len(parts) >= 4 and parts[1] == "revive":
                from ..models.router import revive_key as _rk
                console.print(f"[green]{_rk(parts[2], parts[3])}[/]")
                continue
            console.print("[dim]Usage: /keys add <provider> <key> | /keys list | /keys revive <provider> <n>[/]")
            continue
        if task.startswith("/effort"):
            parts = task.split()
            if len(parts) < 2:
                console.print(f"[dim]Effort: {get_effort()} (low|medium|high)[/]")
                console.print("[dim]Use: /effort low|medium|high — reasoning depth (temperature + max_tokens)[/]")
                continue
            console.print(f"[green]{set_effort(parts[1])}[/]")
            continue
        if task == "/tree":
            from ..trace import recent as _tr_all
            rows = _tr_all(30)
            if not rows:
                console.print("[dim]Koi trace nahi — pehla task chalao.[/]")
                continue
            runs = {}
            for e in rows:
                runs.setdefault(str(e.get("run", "?")), []).append(e)
            for rid, evs in runs.items():
                console.print(f"[bold {th.ACCENT}]run {rid}[/]")
                for e in evs:
                    if e.get("kind") == "observation":
                        console.print(f"  ├─ [dim]{e.get('tool', '?')}[/] {str(e.get('args', ''))[:50]} → {str(e.get('result', ''))[:60]}")
                    else:
                        st = "[green]done[/]" if e.get("status") == "done" else f"[yellow]{e.get('status', '?')}[/]"
                        console.print(f"  └─ {str(e.get('task', ''))[:50]} [{e.get('mode', '')}/{e.get('endpoint', '')}] {st}")
            continue
        if task.startswith("/review"):
            from ..skills import files as _rf
            parts = task.split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                console.print("[dim]Use: /review <file> — outline + syntax + checklist review[/]")
                continue
            fp = parts[1].strip()
            out = _rf.read_file(fp, max_chars=1500)
            ol = _rf.outline(fp)
            chk = ["syntax (py_compile)", "error handling", "permission-gated ops",
                   "secrets exposure", "edge cases (empty/large input)"]
            try:
                import py_compile, tempfile, os as _os
                _tmp = None
                _real = _rf._safe(fp)
                if _real and _real.endswith(".py"):
                    py_compile.compile(_real, doraise=True)
                    chk[0] += " OK"
                else:
                    chk[0] += " n/a (py nahi)"
            except Exception as e:
                chk[0] += f" FAIL: {e}"[:100]
            console.print(Panel(f"{out[:800]}\n---\n{ol[:800]}",
                                title=f" Review: {fp}", border_style=th.ACCENT, padding=(0, 1)))
            for c in chk:
                mark = "[green]✓[/]" if c.endswith("OK") else ("[red]✗[/]" if "FAIL" in c else "[yellow]•[/]")
                console.print(f"  {mark} {c}")
            try:
                from ..models.router import try_chat as _tc
                _, txt = _tc([
                    {"role": "system", "content": "Tum code reviewer ho. 3 line me kami/khatra batao (Hindi)."},
                    {"role": "user", "content": f"FILE: {fp}\n{out[:1000]}"}])
                if txt:
                    console.print(f"[bold]Reviewer:[/] {txt[:300]}")
            except Exception:
                pass
            continue
        if task.startswith("/research"):
            parts = task.split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                console.print("[dim]Use: /research <query> — explorer role se read-only codebase research[/]")
                continue
            res = _run_with_live(f"explore karo: {parts[1].strip()}")
            show_result(res)
            continue
        if task.startswith("/bg"):
            parts = task.split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                console.print("[dim]Use: /bg <task> — background + live-todo + beech me note/cancel[/]")
                continue
            _run_bg(parts[1].strip())
            continue
        if task.startswith("/cache"):
            from ..skills import promptcache as _pc
            parts = task.split()
            if len(parts) > 1 and parts[1] == "clear":
                console.print(f"[green]{_pc.clear()}[/]")
                continue
            n, s = _pc.stats()
            console.print(f"[dim]Prompt cache: {n} entries, ~{s} tokens saved (TTL 24h)[/]")
            console.print("[dim]Use: /cache clear · off: economy.cache=false[/]")
            continue
        if task.startswith("/lsp"):
            from ..skills import lsp as _lsp
            parts = task.split()
            if len(parts) < 2 or parts[1] not in ("diag", "hover", "def"):
                console.print("[dim]Use: /lsp diag <file> | /lsp hover <file:line:col> | /lsp def <file:line:col>[/]")
                console.print("[dim]LSP server chahiye (PC: pyright). Nahi to py_compile fallback.[/]")
                continue
            if parts[1] == "diag":
                tgt = parts[2] if len(parts) > 2 else ""
                if not tgt:
                    console.print("[dim]Use: /lsp diag <file>[/]")
                    continue
                from ..skills import project as _pj
                console.print(Panel(f"{_lsp.diagnose(tgt)}\n---\n{_pj.lint_file(tgt)[:300]}",
                                    title=f" LSP diag: {tgt}", border_style=th.ACCENT, padding=(0, 1)))
                continue
            try:
                fp, lc = parts[2].rsplit(":", 2)[0], parts[2].rsplit(":", 2)[1:]
                ln, cc = int(lc[0]) - 1, int(lc[1])
            except Exception:
                console.print("[dim]Use: /lsp hover <file:line:col>[/]")
                continue
            method = "hover" if parts[1] == "hover" else "definition"
            console.print(Panel(_lsp.symbol_info(fp, ln, cc, method)[:1200],
                                title=f" LSP {parts[1]}: {parts[2]}",
                                border_style=th.ACCENT, padding=(0, 1)))
            continue
        if task.startswith("/comment-zh"):
            from ..skills import zhcomment as _zh
            parts = task.split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                console.print("[dim]Use: /comment-zh <file> — Chinese comments, code unchanged[/]")
                continue
            console.print(f"[green]{_zh.comment_file(parts[1].strip(), ask_cb=ask_main)}[/]")
            continue
        if task == "/reflect":
            from ..skills import reflect as _rf
            rows = _rf.load_last(5)
            if not rows:
                console.print("[dim]Koi reflection nahi — bada task chalao.[/]")
                continue
            for r in rows:
                console.print(Panel(r[:400], border_style="dim", padding=(0, 1)))
            continue
        if task.startswith("/fresh"):
            from .. import workflows as _wf
            parts = task.split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                console.print("[dim]Use: /fresh <ticket> — branch + 5-phase plan cycle[/]")
                continue
            ticket = parts[1].strip()
            br = _wf.fresh_branch(ticket)
            from ..skills import git as _gg
            code, out = _gg._git(["checkout", "-b", br])
            console.print(f"[green]Branch: {br}[/] [dim]{out[:100]}[/]" if code == 0
                          else f"[yellow]{out[:150]}[/]")
            for st in _wf.fresh_plan(ticket):
                console.print(f"  [dim]→ {st[:90]}[/]")
            console.print("[dim]Execute ke liye task likho ya /approve ke baad plan chalao.[/]")
            continue
        if task.startswith("/ship"):
            from .. import workflows as _wf2
            from ..skills import git as _gg2
            from ..planner import read as _pread
            parts = task.split(" ", 1)
            msg = _wf2.ship_message(parts[1] if len(parts) > 1 else _pread())
            console.print(f"[green]{_gg2.auto_commit(msg, ask_cb=ask_main)}[/]")
            code, out = _gg2._git(["push", "-u", "origin", "HEAD"])
            console.print(f"[green]Pushed[/] [dim]{out[:120]}[/]" if code == 0
                          else f"[yellow]Push nahi hua: {out[:150]}[/]")
            continue
        if task == "/autopilot":
            from .. import workflows as _wf3
            from ..scheduler import due as _due, mark_done as _done
            jobs = _due()
            picks = _wf3.autopilot_pick(jobs)
            if not picks:
                console.print("[dim]Koi due job nahi — /schedule se add karo.[/]")
                continue
            for t in picks:
                console.print(f"[bold]Autopilot:[/] {t[:70]}")
                try:
                    res = _run_with_live(t)
                except KeyboardInterrupt:
                    console.print(f"\n[yellow]{_t('task_cancelled')}[/]")
                    break
                show_result(res)
                _done(t)
                if res.get("status") == "denied":
                    console.print("[yellow]Permission deny — autopilot roka.[/]")
                    break
            continue
        try:
            res = _run_with_live(task)
        except KeyboardInterrupt:
            console.print(f"\n[yellow]{_t('task_cancelled')}[/]")
            continue
        show_result(res)
