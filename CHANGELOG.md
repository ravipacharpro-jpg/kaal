# Kaal Changelog

## v0.6.0 — security-audit batch (K-01..K-06, external audit)
- Fixed K-02 (High): symlink traversal — `_safe()` ab realpath-compare (read/write/edit verified-blocked)
- Fixed K-01 (High): RPC `prompt/run` + `prompt/stream` session_id bind karte hain, unknown reject
- Fixed K-03: cancel pe status `cancelled` (khali done-summary nahi)
- Fixed K-04: LSP deterministic cleanup (terminate→wait→kill→close+wait)
- Fixed K-05: `requirements-dev.txt` (pytest), harness me runner-missing ERROR
- Fixed K-06: `trace.warn()` — checkpoint/persist/hook failures ab logged

## v0.6.0 — smart-load batch (task-wise + i18n)
- Added: lazy tool-spec — task ko sirf relevant tools (~60% context bachat, measured)
- Added: i18n (hi/en/zh) + `/lang` — naya UI text `t()` se, Hindi default
- Commands doc regen (40)
- Added: `/dashboard` — status+sessions+keys side-by-side (narrow pe stacked)
- Result footer me session spend + cache saved (cost transparency)
- Commands doc regen (39), footer hint me /dashboard

## v0.6.0 — premium-repo batch
- README hero: badges, real demo output, comparison table, docs links
- `docs/COMMANDS.md` (palette-generated, 38), `docs/ARCHITECTURE.md` (mermaid)
- GitHub issue/PR templates; khali stray dirs saaf
- Added: capability matrix + live binary probes (`platform_adapt.capabilities()`)
- Added: `/platform` command (matrix + probes table)
- Index cap: Termux 60 files, PC 200 (OOM guard)
- README me platform matrix table
- RPC extended: prompt/stream (chunks), session/cancel + interject (worker threads), fs read/write (approve-gated), availableCommands
- LSP: hover/definition via generic stdio client + `/lsp diag|hover|def` (py_compile fallback)
- Palette + footer me `/lsp`

## v0.6.0 — parallel-engine batch (PC track)
- Added: task-graph engine (`kaal/parallel.py` — DAG levels, risky-chain, ordered aggregate, cancel)
- Legacy multi-path ab graph engine use karta hai (writes kabhi parallel nahi)
- Worktree isolation v2 roadmap (cwd plumbing chahiye)
- Added: Skill protocol core (`skills/base.py` — register/hooks/tools-merge, fail-soft)
- Added: prompt-cache (SHA-256 SQLite, TTL 24h, try_chat/try_llm wired, `/cache`)
- Added: zh-comment (`/comment-zh`, code-unchanged verifier)
- Added: reflections (session-end LLM summary, last-3 brain context, `/reflect`)
- Added: CN providers — deepseek/kimi/glm/tongyi (URLs + models + setup + /key)
- Added: saver gate (sequential tools at 80%+), English-only code rule in SYSTEM
- Note: spec me SKILL 2 missing tha (1→3 jump) — kuch implement nahi kiya
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
