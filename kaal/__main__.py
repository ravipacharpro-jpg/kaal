"""kaal CLI entry. TUI default; flags: --history, --resume, --schedule, direct task."""
import sys
from rich.console import Console

console = Console()

def main():
    args = sys.argv[1:]
    if args and args[0] == "--history":
        from .memory.store import recent
        rows = recent(10)
        if not rows:
            console.print("Memory khaali — pehla task karo.")
            return
        for i, (t, s) in enumerate(rows, 1):
            console.print(f"{i}. {t[:60]}\n   → {s[:100]}")
        return
    if args and args[0] == "--resume":
        from .memory.store import recent
        from .agent import run_task
        rows = recent(1)
        if not rows:
            console.print("Resume ke liye koi session nahi.")
            return
        console.print(f"↩️ Resume: {rows[0][0][:80]}")
        res = run_task(rows[0][0], live_cb=print, ask_cb=lambda q: True)
        console.print(f"✅ {res['summary']} (via {res['endpoint']})")
        return
    if args and args[0] == "--telegram":
        from .bridge_telegram import serve
        console.print(serve())
        return
    if args and args[0] == "--schedule":
        from .scheduler import run_due
        from .agent import run_task
        for line in run_due(lambda t: run_task(t, ask_cb=lambda q: True)["summary"][:150]):
            console.print(line)
        return
    if args and args[0] == "--serve":
        import time
        from .scheduler import run_due
        from .agent import run_task
        secs = int(args[1]) if len(args) > 1 and args[1].isdigit() else 300
        console.print(f"🤖 Kaal serve mode — har {secs}s due jobs (Ctrl+C stop). Termux pe Termux:API/cron behtar.")
        try:
            while True:
                for line in run_due(lambda t: run_task(t, ask_cb=lambda q: True)["summary"][:150]):
                    console.print(line)
                time.sleep(secs)
        except KeyboardInterrupt:
            console.print("Serve band.")
        return
    if args:
        from .tui.app import show_header
        from .agent import run_task
        show_header()
        res = run_task(" ".join(args), live_cb=print, ask_cb=lambda q: True)
        console.print(f"✅ {res['summary']} (via {res['endpoint']})")
    else:
        from .tui.app import main_loop
        try:
            main_loop()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
