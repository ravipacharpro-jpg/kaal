"""kaal CLI entry."""
import sys
from .tui.app import main_loop, show_header
from rich.console import Console

def main():
    if len(sys.argv) > 1:
        from .agent import run_task
        res = run_task(" ".join(sys.argv[1:]), live_cb=print, ask_cb=lambda q: True)
        Console().print(f"✅ {res['summary']} (via {res['endpoint']})")
    else:
        try:
            main_loop()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
