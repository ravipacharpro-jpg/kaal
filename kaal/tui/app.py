"""Kaal premium Rich TUI — OpenCode style.
Todo panel + 1-line live, summary only (no code dump).
Wide screen = side-by-side, Termux narrow = stacked.
"""
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from ..agent import run_task
from ..agents.orchestrator import PERSONAS as AGENT_PERSONAS
from ..config_store import get_all as cfg_all, set_perm as cfg_set_perm
from ..memory.store import recent
from ..models.ollama import status_line
from ..models.ollama import PRESETS as OLLAMA_PRESETS, pull as ollama_pull, detect as ollama_detect
from ..models.router import add_user_key, budget_status, list_endpoints
from ..models.router import POPULAR_MODELS, get_model, set_model
from ..models.router import get_role_model, set_role_model
from ..platform_adapt import describe as plat_describe
from ..scheduler import add as sched_add, due as sched_due
from ..storage import startup_check
from . import theme as th

console = Console()


def _status_strip():
    parts = []
    try:
        b = budget_status()
        parts.append(f"💰 {b['used']}/{b['budget']} · {b['mode']}")
    except Exception:
        pass
    try:
        eps = list_endpoints()
        parts.append(f"📡 {len(eps)} endpoints")
    except Exception:
        pass
    try:
        parts.append(plat_describe().replace("⚙️ ", ""))
    except Exception:
        pass
    return "  │  ".join(parts)


def show_header():
    console.print(Panel(
        Align.center(Text.from_markup(
            f"[bold {th.ACCENT}]🤖 KAAL[/]  [dim]— Ahead of Time[/]\n"
            "[dim]autonomous agent · Termux / Linux / macOS / Windows[/]")),
        border_style=th.ACCENT, padding=(1, 4)))
    console.print(f"[dim]{_status_strip()}[/]")
    try:
        console.print(f"[dim]{startup_check()}[/]")
    except Exception:
        pass
    console.print(Rule(style="dim"))
    console.print(th.FOOTER_HINT + "\n")


def show_endpoints():
    t = Table(title="📡 Endpoints", show_header=True,
              header_style=f"bold {th.ACCENT}", border_style="dim",
              show_lines=False)
    t.add_column("#", style="dim", width=3)
    t.add_column("Endpoint", style="bold")
    t.add_column("Limit", justify="right")
    t.add_column("Desc", style="dim")
    for i, e in enumerate(list_endpoints(), 1):
        lim = "∞" if e["daily_limit"] == -1 else str(e["daily_limit"])
        mark = "● " if i == 1 else "○ "
        t.add_row(str(i), mark + e["name"], lim, e["desc"][:44])
    console.print(Panel(t, border_style="dim", padding=(0, 1)))
    console.print(f"[dim]{status_line()}[/]")


def show_todos(todos):
    t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
              border_style="dim", box=None, pad_edge=False)
    t.add_column("", width=2)
    t.add_column("Kaam", style="bold")
    t.add_column("Agent", style="magenta")
    t.add_column("Status", justify="right")
    icon = {"pending": "[dim]○[/]", "doing": "[yellow]→[/]", "done": "[green]✓[/]"}
    for td in todos:
        t.add_row(icon.get(td["status"], "?"), td["title"][:46],
                  td.get("agent", "-")[:14], td["status"])
    return Panel(t, title="[bold]Todo[/]", border_style=th.ACCENT, padding=(0, 1))


def show_result(res):
    wide = console.width >= 100
    body = Group(
        Markdown(res["summary"][:600]),
        Text(f"via {res['endpoint']} · {res.get('mode', 'single')} · "
             f"{res.get('budget', '')} · memory saved",
             style="dim"),
    )
    result = Panel(body, title="[bold green]✅ Result[/]",
                   border_style=th.OK, padding=(1, 2))
    todos = show_todos(res["todos"])
    if wide:
        console.print(Columns([todos, result], equal=True, expand=True))
    else:
        console.print(todos)
        console.print(result)
    console.print(Rule(style="dim"))


def show_budget():
    b = budget_status()
    pct = b["pct"]
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    console.print(Panel(
        f"[bold]{bar}[/]  {b['used']}/{b['budget']} tokens ({pct}%)\n"
        f"⚡ policy: [bold]{b['mode']}[/]",
        title="💰 Budget", border_style=th.WARN, padding=(1, 2)))


def show_memory():
    rows = recent(5)
    if not rows:
        console.print("[dim]Memory khaali — pehla task karo.[/]")
        return
    t = Table(show_header=True, header_style=f"bold {th.ACCENT}",
              border_style="dim", box=None)
    t.add_column("Task", style="bold")
    t.add_column("Summary", style="dim")
    for task, summ in rows:
        t.add_row(task[:44], summ[:64])
    console.print(Panel(t, title="🧠 Memory", border_style=th.ACCENT, padding=(0, 1)))


def show_agents():
    t = Table(show_header=False, border_style="dim", box=None)
    t.add_column("Agent", style="bold magenta")
    t.add_column("Persona", style="dim")
    for a, role in AGENT_PERSONAS.items():
        if a == "general":
            continue
        t.add_row("⬢ " + a, role[:70])
    console.print(Panel(t, title="🤖 Agents", border_style="magenta", padding=(0, 2)))


def _run_with_live(task):
    from ..models.router import estimate
    try:
        console.print(f"[dim]💰 Cost estimate: {estimate(task)}[/]")
    except Exception:
        pass
    live = {"msg": "soch raha hu..."}
    with Progress(SpinnerColumn(style=th.ACCENT),
                   TextColumn("⚡ {task.fields[live]}"),
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
            live["msg"] = f"💭 {tail}"
            prog.update(pt, live=live["msg"])

        res = run_task(task, live_cb=wrap,
                       ask_cb=lambda q: Confirm.ask(f"⚠️  {q}"),
                       on_token=stream_wrap,
                       ask_text_cb=lambda q: Prompt.ask(f"[bold yellow]❓ {q}[/]"))
        prog.update(pt, completed=100)
    return res


def main_loop():
    show_header()
    while True:
        try:
            task = Prompt.ask("[bold green]❯[/]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Kaal band. Phir milenge.[/]")
            break
        if not task:
            continue
        if task in ("/quit", "/q", "quit"):
            console.print("[yellow]Kaal band.[/]")
            break
        if task == "/endpoints":
            show_endpoints()
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
            console.print(Panel(_who() or "[dim]Khaali.[/]", title="👤 USER + MEMORY",
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
            parts = task.split(" ", 2)
            if len(parts) < 3:
                jobs = sched_due()
                console.print(f"[dim]Due jobs: {len(jobs)}[/]")
                for j in jobs[:5]:
                    console.print(f"⏰ {j['task'][:60]}")
                console.print("[dim]Use: /schedule 86400 task yahan[/]")
                continue
            try:
                console.print(f"[green]{sched_add(parts[2], int(parts[1]))}[/]")
            except ValueError:
                console.print("[red]Interval number me do: /schedule 86400 task[/]")
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
                console.print(Panel(t, title="🔐 Permissions",
                                    border_style=th.ACCENT, padding=(0, 1)))
                console.print("[dim]Use: /perm delete_files allow|ask|deny[/]")
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
                    console.print(Panel(t, title="🔌 Plugins", border_style=th.ACCENT))
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
            console.print("[dim]🎤 Bolo... (sun raha hu)[/]")
            try:
                r = subprocess.run(["termux-speech-to-text"], capture_output=True,
                                   text=True, timeout=30)
                heard = r.stdout.strip()[:300]
            except Exception as e:
                heard = ""
            if not heard:
                console.print("[dim]Kuch sunai nahi diya.[/]")
                continue
            console.print(f"[bold]🎤 Suna: {heard}[/]")
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
            th = thread_context()
            console.print(Panel(th or "[dim]Thread khaali.[/]", title="🧵 Thread",
                                border_style=th.ACCENT, padding=(0, 1)))
            continue
        if task.startswith("/plan"):
            from ..planner import draft, write, read as plan_read
            what = task[5:].strip()
            if not what:
                cur = plan_read()
                console.print(Panel(cur or "[dim]Koi plan nahi. Use: /plan task yahan[/]",
                                    title="📋 PLAN.md", border_style=th.ACCENT))
                continue
            steps = draft(what)
            write(what, steps)
            t = Table(show_header=False, border_style="dim", box=None)
            t.add_column("#", style="dim"); t.add_column("Step", style="bold")
            for i, s in enumerate(steps, 1):
                t.add_row(str(i), s[:70])
            console.print(Panel(t, title=f"📋 Plan: {what[:50]}", border_style=th.ACCENT))
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
                console.print(Panel("🍳 " + " | ".join(list_all() or ["koi nahi"]),
                                    title="Recipes", border_style=th.ACCENT))
                console.print("[dim]Use: /recipe morning-review[/]")
                continue
            steps = recipe_get(parts[1].strip())
            if not steps:
                console.print("[red]Recipe mili nahi.[/]")
                continue
            for s in steps:
                console.print(f"[dim]🍳 {s[:70]}[/]")
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
                    title=f"🦙 Ollama ({'live ✅' if ok else 'band — `ollama serve` karo'})",
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
                console.print(Panel(t, title="🧠 Models (OpenRouter 75+ via openrouter key)",
                                    border_style=th.ACCENT, padding=(0, 1)))
                console.print("[dim]Use: /model 5 · /model architect 3 · /model editor 5[/]")
                continue
            name = parts[1].strip()
            pick = POPULAR_MODELS[int(name) - 1] if name.isdigit() and 1 <= int(name) <= len(POPULAR_MODELS) else name
            console.print(f"[green]{set_model(pick)}[/]")
            continue
        res = _run_with_live(task)
        show_result(res)
