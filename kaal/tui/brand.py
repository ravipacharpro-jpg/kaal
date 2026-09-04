"""Kaal brand — premium ASCII banner (Nexus-grade look, Rich markup).
No circular imports. Uses Rich colour names as strings.
"""
NAME = "kaal"
VERSION = "v0.6.0"
TAGLINE = "autonomous agent · ahead of time"

BIG = """[bold cyan]  ██╗  ██╗ █████╗  █████╗ ██╗     
  ██║ ██╔╝██╔══██╗██╔══██╗██║     
  █████╔╝ ███████║███████║██║     
  ██╔═██╗ ██╔══██║██╔══██║██║     
  ██║  ██╗██║  ██║██║  ██║███████╗
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝[/]"""

BANNER = BIG + """
[dim]       ◇       ◇       ◇
       │       │       │
[/][cyan]   ╭───────┬───────┬───────╮
   │[/][white] THINK [/][cyan]│[/][bold cyan] ACT  [/][cyan]│[/][green] VERIFY[/][cyan]│
   ╰───────┴───────┴───────╯[/]
[cyan]             ●[/][dim]  KAAL · POWER CORE · {version}
     KAAL ...Autonomous agent, ahead of time![/]""".format(version=VERSION)


def agent_name():
    """Return the premium agent name badge."""
    return NAME


def brand():
    """Render the branded banner (returns rich markup string, Panel is caller's job)."""
    # Return markup so show_header can decide Panel/border
    return BANNER