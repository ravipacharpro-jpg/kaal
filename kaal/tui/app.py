"""Kaal premium Rich TUI — Todo panel + 1-line live, no code dump.
Termux compact, PC 2-column. Cross-platform.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, BarColumn, TextColumn
from ..agent import run_task
from ..models.router import list_endpoints, budget_status, add_user_key
from ..models.ollama import status_line
from ..memory.store import recent
from ..agents.specialists import AGENTS
from ..scheduler import add as sched_add, due as sched_due

console = Console()

def show_header():
    console.print(Panel.fit("🤖 [bold cyan]KAAL[/] — [dim]samay se aage[/]\n[dim]Termux / Linux / macOS / Windows[/]",
                            border_style="cyan"))

def show_endpoints():
    t = Table(title="Endpoints (free-tier first)", show_header=True)
    t.add_column("#"); t.add_column("Endpoint"); t.add_column("Limit"); t.add_column("Desc")
    for i, e in enumerate(list_endpoints(), 1):
        lim = "∞" if e["daily_limit"] == -1 else str(e["daily_limit"])
        t.add_row(str(i), e["name"], lim, e["desc"][:40])
    console.print(t)
    console.print(f"[dim]{status_line()}[/]")

def show_todos(todos):
    t = Table(title="Todo", show_header=True)
    t.add_column("#"); t.add_column("Kaam"); t.add_column("Agent"); t.add_column("Status")
    icon = {"pending": "○", "doing": "→", "done": "✓"}
    for i, td in enumerate(todos, 1):
        t.add_row(str(i), td["title"][:40], td.get("agent", "-")[:12], icon.get(td["status"], "?"))
    console.print(t)

def show_budget():
    b = budget_status()
    console.print(Panel(f"💰 {b['used']}/{b['budget']} tokens | {b['pct']}% | ⚡ {b['mode']}",
                        title="Budget", border_style="yellow"))

def show_memory():
    rows = recent(5)
    if not rows:
        console.print("[dim]Memory khaali — pehla task karo.[/]")
        return
    t = Table(title="Memory (recent)", show_header=True)
    t.add_column("Task"); t.add_column("Summary")
    for task, summ in rows:
        t.add_row(task[:40], summ[:60])
    console.print(t)

def show_agents():
    console.print(Panel("🤖 " + " | ".join(AGENTS), title="Agents", border_style="magenta"))

def main_loop():
    show_header()
    console.print("[dim]Commands: /endpoints /budget /memory /agents /key /schedule /quit | seedha task likho[/]\n")
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
                console.print("[dim]Use: /key openai sk-... (provider: openai groq openrouter together mistral gemini xai)[/]")
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
        live_line = {"msg": "soch raha hu..."}
        def live_cb(m): live_line["msg"] = m
        with Progress(TextColumn("⚡ {task.fields[live]}"), BarColumn(),
                      TextColumn("{task.percentage:.0f}%"),
                      console=console, transient=True) as prog:
            pt = prog.add_task("live", total=100, live=live_line["msg"])
            def wrap(m):
                live_line["msg"] = m
                prog.update(pt, live=m)
            res = run_task(task, live_cb=wrap,
                           ask_cb=lambda q: Confirm.ask(f"⚠️  {q}"))
            prog.update(pt, completed=100)
        show_todos(res["todos"])
        console.print(Panel(f"[green]{res['summary']}[/]\n[dim]via {res['endpoint']} | {res.get('mode','single')} | {res.get('budget','')} | memory saved[/]",
                            title="✅ Result", border_style="green"))
