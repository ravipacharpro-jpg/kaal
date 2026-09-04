"""Fullscreen screen — Nexus-style layout with Rich (no new deps).
Left: history (thoughts + results + todos). Right sidebar: session, context,
LSP, Todo. Bottom: input box visual + model line + hints + version bar.
Static redraw model (clear + render each turn) — Termux-safe, no alt-screen.
"""
from rich.align import Align
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import theme as th


def _sidebar(state):
    d = state.get("dash", {}) or {}
    rows = []
    rows.append("[bold]Session[/]")
    rows.append(f"[dim]{state.get('session_id', 'new')}[/]")
    rows.append("")
    rows.append("[bold]Context[/]")
    rows.append(f"[dim]{d.get('budget', '?')} used[/]")
    rows.append("")
    rows.append("[bold]LSP[/]")
    rows.append(f"[dim]{d.get('lsp', '?')}[/]")
    rows.append("")
    rows.append("[bold]Todo[/]")
    todos = state.get("todos", []) or []
    if not todos:
        rows.append("[dim][ ] no active task[/]")
    for td in todos[-8:]:
        mark = {"pending": "[ ]", "doing": "[>]", "done": "[x]"}.get(
            td.get("status", "pending"), "[ ]")
        mark = mark.replace("[", "\\[").replace("]", "\\]")
        color = {"pending": "dim", "doing": "yellow", "done": "green"}.get(
            td.get("status", "pending"), "dim")
        rows.append(f"[{color}]{mark}[/] {str(td.get('title', ''))[:30]}")
    return Panel("\n".join(rows), title=" Kaal", border_style="dim",
                 padding=(0, 1))


def _main(state):
    parts = []
    hist = state.get("history", []) or []
    if not hist:
        parts.append("[dim]Welcome — seedha task likho, ya /dashboard, /palette.[/]")
    for h in hist[-12:]:
        kind = h.get("kind", "text")
        if kind == "thought":
            parts.append(f"[dim]Thought · {h.get('secs', '?')}[/]")
        elif kind == "task":
            parts.append(f"[bold]› {h.get('text', '')[:100]}[/]")
        elif kind == "result":
            parts.append(str(h.get('text', ''))[:500])
        elif kind == "notice":
            parts.append(f"[yellow]{h.get('text', '')[:150]}[/]")
    return Panel("\n\n".join(parts) if parts else "[dim]...[/]",
                 border_style="dim", padding=(0, 1))


def _input_box(state):
    from rich.box import Box as _Box
    d = state.get("dash", {}) or {}
    model = str(d.get("model", "auto"))
    # Nexus-style: left accent border only (no full box)
    _left = _Box("    \n    \n    \n│   \n    \n    \n    \n    ")
    inner = Text("Ask anything...  (type + Enter)", style="dim")
    box = Panel(inner, box=_left, border_style="magenta", padding=(0, 2))
    meta = Text(f"kaal · {model} · {d.get('effort', 'medium')}", style="magenta")
    hints = Text("/agents  ctrl+p commands  /dashboard", style="dim")
    return [box, Align.center(meta), Align.center(hints)]


def _status_bar(state, width=80):
    d = state.get("dash", {}) or {}
    try:
        from .brand import VERSION as _V
    except Exception:
        _V = ""
    left = "~"
    right = f"session {d.get('session', '?')} · ctx {d.get('budget', '?')} · KAAL {_V}"
    gap = max(1, width - len(left) - len(right) - 2)
    return Text(left + " " * gap + right, style="dim")


def render(state, console=None):
    """Full screen Layout. state: {history[], todos[], dash{}, session_id}.
    Narrow (<90): sidebar neeche stack (Termux portrait safe)."""
    try:
        from rich.console import Console as _C
        width = (console.width if console else None) or _C().width
    except Exception:
        width = 80
    lay = Layout(name="screen")
    items = _input_box(state)
    if width >= 90:
        top = Layout(name="top")
        top.split_row(
            Layout(_main(state), name="main", ratio=1),
            Layout(_sidebar(state), name="side", size=32),
        )
    else:
        top = Layout(_main(state), name="main", ratio=1)
    lay.split_column(top, Layout(name="bottom", size=8))
    lay["bottom"].split_column(
        Layout(items[0], name="i", size=3),
        Layout(items[1], name="m", size=1),
        Layout(items[2], name="h", size=1),
        Layout(_status_bar(state, width), name="s", size=1),
    )
    return lay
