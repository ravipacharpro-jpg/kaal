# Kaal — Ahead of Time

![tests](https://github.com/ravipacharpro-jpg/kaal/actions/workflows/test.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![platform](https://img.shields.io/badge/platform-Termux%20%7C%20Linux%20%7C%20macOS%20%7C%20Windows-green)
![license](https://img.shields.io/badge/license-MIT-lightgrey)
![version](https://img.shields.io/badge/version-v0.6.0-cyan)

Autonomous AI coding agent — **phone pe bhi, PC pe bhi.** API key ya local Ollama ho to LLM brain, nahi to fast keyword path (AI nahi — neeche Design me saaf likha hai).

```bash
$ kaal --mode json "file list memory"
{"task": "file list memory", "result": {"status": "done", "summary": " [general] file list memory: ... me 25 cheez: .git, .github, .gitignore ...", "endpoint": "omniroute/auto", "mode": "single"}}
```

## Kyun Kaal? (competitors se alag)
| | Kaal | Claude Code / OpenCode |
|---|---|---|
| Phone (Termux) pe chalta hai | ✅ | ❌ |
| ₹0 me autonomous (free-tier rotation + cache) | ✅ | ❌ (paid ya key lao) |
| Self-healing keys (dead auto-kick + revive) | ✅ | ❌ |
| Har release SWE-score ke saath | ✅ (`benchmarks/`) | chhupate hain |
| Zero heavy deps (stdlib-first) | ✅ | ❌ (node/bun stack) |

## Install
```bash
# Termux / Linux / macOS
git clone https://github.com/ravipacharpro-jpg/kaal.git
cd kaal
bash install/install.sh
# phir: kaal  (ya python3 -m kaal)
```
```bat
REM Windows (cmd, Python 3.11+)
git clone https://github.com/ravipacharpro-jpg/kaal.git
cd kaal
install\install.bat
REM phir: install\kaal.bat  (ya python -m kaal)
```

## Use
```bash
kaal                                   # interactive TUI
kaal "file read README.md"             # direct task
kaal "github repo ravipacharpro-jpg/kaal check karo"
kaal --history                         # pichle sessions dekho
kaal --resume                          # last task dobara chalao
kaal --schedule                        # due scheduled jobs chalao
```

TUI commands (43 — poori list: [`docs/COMMANDS.md`](docs/COMMANDS.md), palette: Ctrl+P): `/palette` `/dashboard` `/lang` `/setup` `/endpoints` `/platform` `/budget` `/memory` `/agents` `/key` `/model` `/effort` `/ollama` `/schedule` `/perm` `/plan` `/approve` `/review` `/research` `/bg` `/fresh` `/ship` `/autopilot` `/theme` `/session` `/checkpoint` `/rewind` `/tree` `/trace` `/thread` `/export` `/logs` `/zoom` `/clean` `/sandbox` `/quit`

```bash
/key openai sk-...          # unlimited API add (same provider multiple allowed)
/perm delete_files allow    # permission: ask|allow|deny
/schedule 86400 task        # roz auto-chalne wala kaam
```

## Design (honest)
- **TUI (Rich):** Todo auto `○/→/✓` + agent column, fixed 1-line live, summary only (code dump nahi)
- **Brain 2 modes:** vault API key ho YA Ollama local chal raha ho to LLM tool-loop (26 tools, clarify+review, parallel reads, personas + few-shot + self-correction + streaming + context-compress + thread + USER/MEMORY); nahi to keyword rule path (fast, par AI nahi — seedha likha hai)
- **Endpoints:** 20 configured targets + deepseek/kimi/glm/tongyi (CN LLMs); bina key wale call nahi hote (sirf list) — key `/key` se add karo ya Ollama chalao. `ollama_local` hi real keyless hai.
- **Routing:** keyword classify + specialist personas; reasoning LLM karta hai, router nahi
- **Sandbox:** AST-verified (import/open/eval/dunder block) + optional docker (PC). OS-level boundary nahi — sensitive machine pe `/perm` tight rakho.
- **Safety:** L1/L2/L3 autonomy (scheduled default L1 report-only, `--unattended` = L3), unattended auto-DENY, `[UNTRUSTED]` injection marking + prompt guard, AST sandbox, secret-scan pre-commit, vault 0600 + optional AES (`cryptography` ho to, PC pe), self-healing keys (3x auth-fail/quota → dead, `/keys revive`)
- **Skills:** files (backup STACK + undo N + checkpoints + fuzzy + syntax-verify + highlighted diff), code (AST sandbox/docker), repl (persistent audited namespace), prompt-cache (SHA-256 SQLite, TTL 24h), zh-comment (Chinese comments, code-verify), reflections (cross-session), browser (Playwright/HTTP), GitHub (vault token), git (commit+changelog+secret-scan), bash allowlist, project-detect (+AGENTS.md), code-search (BM25), vision, plugins (+Skill protocol: `SKILL` dict se naya skill bina core chhue)
- **Multi-agent:** 12 personas + LLM role classify (brain mode), task-graph engine (writes chained sequential, reads parallel; PC multi-core, Termux sequential)
- **Economy:** REAL token counts (API usage field), 80% pe saver mode, rate-limit rotation, pre-run estimate, per-session cap (default 2000, brain auto-off)
- **Memory:** SQLite + FTS patterns + TF-IDF ranked search + thread continuity + USER.md/MEMORY.md (editable) + auto-skills + PLAN.md + recipes + session export
- **Serve/vision/bridge:** `--serve` loop + systemd unit (desktop, CI-validated), image_describe (vision key pe), `--telegram` phone bridge (channels/ gateway — discord/whatsapp pattern ready), `/voice` (Termux:API mic)
```bash
kaal --telegram   # phone se task (config/telegram.json me token+ids)
kaal --heartbeat  # cron/Termux:JobScheduler se one-shot due jobs
kaal --daemon 300 # PID file + serve loop (stop: kill, PID file delete)
kaal --mode json "task"  # single task → JSON (pip/tool friendly)
kaal --mode rpc          # JSON-RPC stdio bridge (IDE integration: prompt/stream, session/cancel+interject, fs, commands)
python3 benchmarks/swe_run.py dataset.json --out results.json  # SWE-style grading
```
- **Platform:** Termux/Linux/macOS/Windows, storage quota + auto-clean, `--resume/--history`
  - Philosophy: chhota kam khaye, bada zyada — har platform apni aukat me chalta hai (`/platform` se dekho)
  - | capability | Termux | PC (Linux/macOS/Windows) |
    |---|---|---|
    | parallel agents | 1 (sequential) | 2–4 |
    | docker sandbox | nahi | binary mile to |
    | LSP server | nahi (py_compile fallback) | binary mile to |
    | daemon | cron/JobScheduler | systemd/launchd/manual |
    | code index | capped (60 files) | full (200 files) |
    | voice mic | Termux:API se | nahi |

## Structure
```
kaal/kaal/{__main__,agent,config_store,config_defaults,storage,platform_adapt,scheduler,
  tui/,models/{router,llm,ollama},skills/{files,code,browser},mcp/{registry,github},
  agents/{orchestrator,specialists},memory/{store,patterns}}
config/ install/ memory/ logs/
```

## Status
v0.6.0 — security-audit batch in. Tests 103 pass + benchmark 12/12 (hermetic).
Verify: `kaal "file read README.md"`.

## Docs
- [`docs/COMMANDS.md`](docs/COMMANDS.md) — 38 commands (palette se auto-generated)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layers, data flow, platform gating
- [`CHANGELOG.md`](CHANGELOG.md) — har batch kya laya
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — naya skill 1 file + SKILL dict me
