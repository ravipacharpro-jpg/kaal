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
from ..agents.specialists import AGENTS
from ..config_store import get_all as cfg_all, set_perm as cfg_set_perm
from ..memory.store import recent
from ..models.ollama import status_line
from ..models.router import add_user_key, budget_status, list_endpoints
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
    t.add_column("Role", style="dim")
    roles = {"orchestrator": "task decompose", "coder": "code + review",
             "researcher": "web research", "analyzer": "data + stats",
             "github_specialist": "repos + issues"}
    for a in AGENTS:
        t.add_row("⬢ " + a, roles.get(a, "specialist"))
    console.print(Panel(t, title="🤖 Agents", border_style="magenta", padding=(0, 2)))


def _run_with_live(task):
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

        res = run_task(task, live_cb=wrap,
                       ask_cb=lambda q: Confirm.ask(f"⚠️  {q}"))
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
        res = _run_with_live(task)
        show_result(res)
