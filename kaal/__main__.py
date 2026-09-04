"""kaal CLI entry. TUI default; flags: --history, --resume, --schedule, --heartbeat, --daemon, direct task."""
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
        console.print(f"↩ Resume: {rows[0][0][:80]}")
        res = run_task(rows[0][0], live_cb=print, ask_cb=lambda q: True)
        console.print(f" {res['summary']} (via {res['endpoint']})")
        return
    if args and args[0] == "--telegram":
        from .channels.telegram import serve
        console.print(serve())
        return
    unattended = "--unattended" in args
    args = [a for a in args if a != "--unattended"]

    def _level():
        if unattended:
            return "L3"
        try:
            from .autonomy import get_level
            return get_level()
        except Exception:
            return "L1"

    if args and args[0] == "--schedule":
        from .scheduler import run_due
        from .agent import run_task
        lv = _level()
        console.print(f"[dim]Scheduled mode — autonomy {lv} (L1=report-only, L2=allow-list, L3=full).[/]")
        # Unattended: sensitive auto-DENY + level gate, sirf /perm allow wale chalenge
        for line in run_due(lambda t, level: run_task(t, ask_cb=lambda q: False, level=level)["summary"][:150], lv):
            console.print(line)
        return
    if args and args[0] == "--mode" and len(args) > 1 and args[1] == "rpc":
        from . import rpc as _rpc
        _rpc.serve_stdio()
        return
    if args and args[0] == "--mode" and len(args) > 1 and args[1] == "json":
        from . import rpc as _rpc
        _rpc.run_json(" ".join(args[2:]) or "ping")
        return
    if args and args[0] == "--heartbeat":
        # One-shot due-run — cron / Termux:JobScheduler se chalao (daemon nahi chahiye)
        from .scheduler import run_due
        from .agent import run_task
        lv = _level()
        n = 0
        for line in run_due(lambda t, level: run_task(t, ask_cb=lambda q: False, level=level)["summary"][:150], lv):
            console.print(line)
            n += 1
        console.print(f"[dim]Heartbeat done — {n} job(s), autonomy {lv}.[/]")
        return
    if args and args[0] == "--daemon":
        import os as _os
        pidf = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "config", "kaal.pid"))
        try:
            with open(pidf, "w", encoding="utf-8") as f:
                f.write(str(_os.getpid()))
        except OSError:
            pass
        console.print(f"[dim]Daemon PID {_os.getpid()} → {pidf} (stop: kill + file delete). PC pe systemd unit bhi hai.[/]")
        args = ["--serve"] + args[1:]
    if args and args[0] == "--serve":
        import time
        from .scheduler import run_due
        from .agent import run_task
        secs = int(args[1]) if len(args) > 1 and args[1].isdigit() else 300
        lv = _level()
        console.print(f" Kaal serve mode — har {secs}s due jobs, autonomy {lv} (Ctrl+C stop). Termux pe Termux:API/cron behtar.")
        console.print("[dim]Unattended safety: L1 report-only default; L3 sirf --unattended pe.[/]")
        try:
            while True:
                for line in run_due(lambda t, level: run_task(t, ask_cb=lambda q: False, level=level)["summary"][:150], lv):
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
        console.print(f" {res['summary']} (via {res['endpoint']})")
    else:
        from .tui.app import main_loop
        try:
            import sys as _sys
            if _sys.stdin.isatty():
                from .tui.setup import needs_onboarding, run_setup
                if needs_onboarding():
                    console.print("[dim]Pehli baar? Setup khol raha hu (skip: Ctrl+C).[/]")
                    try:
                        run_setup()
                    except KeyboardInterrupt:
                        console.print("[dim]Setup skip.[/]")
            main_loop()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
