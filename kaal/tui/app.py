"""Kaal premium Rich TUI — Todo panel + 1-line live, no code dump.
Termux compact, PC 2-column. Cross-platform.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, BarColumn, TextColumn
from ..agent import run_task
from ..models.router import list_endpoints, budget_status
from ..memory.store import recent
from ..agents.specialists import AGENTS

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
    console.print("[dim]Commands: /endpoints /budget /memory /agents /quit | seedha task likho[/]\n")
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
