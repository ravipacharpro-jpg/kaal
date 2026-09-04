"""Kaal brand — OpenCode-style premium agent name.
No circular imports. Uses Rich colour names as strings.
"""
NAME = "kaal"
VERSION = "v0.6.0"
TAGLINE = "autonomous agent · ahead of time"


def agent_name():
    """Return the premium agent name badge."""
    return NAME


def brand():
    """Render the branded banner (returns rich markup string, Panel is caller's job)."""
    # Return markup so show_header can decide Panel/border
    return f"[bold cyan]{NAME}[/]  [dim]{TAGLINE}[/]"