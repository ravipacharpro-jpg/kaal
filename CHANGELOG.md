# Kaal Changelog

## v0.6.0 — palette/keys batch
- Added: Command Palette (`/palette`, Ctrl+P) — fuzzy, nested, stdlib-only (termios/msvcrt)
- Added: Setup tab (`/setup`, first-run auto) — masked key input, ping-test, github token in vault
- Added: self-healing keys — fail_count/last_fail/status, quota-exceeded classify, 3x → dead + notice, `/keys revive`, health in `/keys list`
- Fixed: GitHub token ab vault se (LLM-provided token ignore)
- Added: `/theme` (live accent + persist), `/session` (list/resume)
- Fixed: SWE harness stale-`__pycache__` flake (PYTHONDONTWRITEBYTECODE + clear)
- Added: SWE dataset runner — patch apply, FAIL_TO_PASS/PASS_TO_PASS grading, batch + CLI (`benchmarks/swe_run.py dataset.json`)
- Hardened: worktree retry + prune (slow-storage git flakes)
- Note: suite me rare environmental flake (~1/8 runs, SWE worktree tests) — retry se mitigated, root cause still under watch
- Added: `/bg <task>` — background task + live-todo panel + beech me note/cancel
- Added: `step_cb`/`cancel`/`inbox` hooks in `run_task` + brain loop (backward compatible)
- Fixed: `/keys list` ab asal vault dikhata hai (masked, poori key kabhi nahi)
- Ctrl+C graceful everywhere (partial state safe)

## v0.6.0 — maintenance batch
- Fixed: undo/checkpoint timestamp-collision race (monotonic unique stamps + exclusive create)
- Added: trace.jsonl rotation (512KB cap, tail-200 keep)
- Deps pinned with upper bounds (`rich<16`, `requests<3`, `click<9`)
- Version bumped 0.1.0 → 0.6.0, CHANGELOG started

## RPC / perms / LSP batch
- Added: `kaal --mode json` + `--mode rpc` (minimal ACP-style JSON-RPC bridge, `kaal/rpc.py`)
- Added: per-directory permission scopes (longest-prefix match, delete wiring)
- Added: stdlib LSP stdio client (`kaal/skills/lsp.py`, unbuffered-IO fix)
- Added: SWE-bench-style local harness (`benchmarks/swe_run.py`, temp worktree)
- Added: `vscode-kaal/` extension scaffold (untested, PC-only)

## Session / memory / REPL batch
- Added: per-session token cap (default 2000, brain auto-off + note)
- Added: TF-IDF ranked memory search (pure stdlib, no numpy)
- Added: persistent audited REPL skill (`kaal/skills/repl.py`)
- Added: `kaal --heartbeat` (cron-friendly) + `kaal --daemon` (PID file)
- Added: `/fresh` `/ship` `/autopilot` workflows (`kaal/workflows.py`)
- Added: `/effort` (reasoning depth → temperature + max_tokens), `/tree`, `/review`, `/research`
- Added: AGENTS.md/CLAUDE.md project context (auto-inject in brain prompt)
- Added: vault AES-at-rest when `cryptography` present, else plaintext+0600
- Fixed: config paths read `~/config` instead of repo `config/` (7 files)
- Fixed: TUI crash (`th` variable shadowing in `main_loop`)
- Fixed: secrets permission gate bypass (`agent.py`)
- Added: MIT LICENSE, CONTRIBUTING.md, `secrets` perm default

## Earlier (pre-0.6.0, from history)
- L1/L2/L3 autonomy, unattended auto-deny, injection marking, undo stack
- USER/MEMORY.md, auto-skills, telegram bridge, voice, vision
- Real token counts, FTS patterns + thread, serve mode, rewind mtime fix
- BM25 code search, context compress, parallel tools, architect/editor split
- Docker sandbox opt-in, Windows installer, checkpoints/rewind, recipes
- AST sandbox, planner/explorer roles, secret pre-commit scan, streaming
