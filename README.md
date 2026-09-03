# Kaal — Ahead of Time

Fully autonomous AI agent — Termux / Linux / macOS / Windows.
Premium Rich TUI: Todo panel + 1-line live Hindi status, TUI me code dump nahi.

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

TUI commands: `/endpoints` `/budget` `/memory` `/agents` `/key` `/model` `/ollama` `/schedule` `/perm` `/plan` `/approve` `/recipe` `/checkpoint` `/rewind` `/export` `/sandbox` `/quit`

```bash
/key openai sk-...          # unlimited API add (same provider multiple allowed)
/perm delete_files allow    # permission: ask|allow|deny
/schedule 86400 task        # roz auto-chalne wala kaam
```

## Design (honest)
- **TUI (Rich):** Todo auto `○/→/✓` + agent column, fixed 1-line live, summary only (code dump nahi)
- **Brain 2 modes:** vault API key ho YA Ollama local chal raha ho to LLM tool-loop (26 tools, clarify+review, parallel reads, personas + few-shot + self-correction + streaming + context-compress + thread + USER/MEMORY); nahi to keyword rule path (fast, par AI nahi — seedha likha hai)
- **Endpoints:** 20 configured targets; bina key wale call nahi hote (sirf list) — key `/key` se add karo ya Ollama chalao. `ollama_local` hi real keyless hai.
- **Routing:** keyword classify + specialist personas; reasoning LLM karta hai, router nahi
- **Sandbox:** AST-verified (import/open/eval/dunder block) + optional docker (PC). OS-level boundary nahi — sensitive machine pe `/perm` tight rakho.
- **Safety:** L1/L2/L3 autonomy (scheduled default L1 report-only, `--unattended` = L3), unattended auto-DENY, `[UNTRUSTED]` injection marking + prompt guard, AST sandbox, secret-scan pre-commit
- **Skills:** files (backup STACK + undo N + checkpoints + fuzzy + syntax-verify + highlighted diff), code (AST sandbox/docker), browser (Playwright/HTTP), GitHub, git (commit+changelog+secret-scan), bash allowlist, project-detect, code-search (BM25), vision, plugins
- **Multi-agent:** 5 personas + LLM role classify (brain mode), desktop pe parallel, Termux pe sequential
- **Economy:** REAL token counts (API usage field), 80% pe saver mode, rate-limit rotation, pre-run estimate
- **Memory:** SQLite + FTS patterns + thread continuity + USER.md/MEMORY.md (editable) + auto-skills + PLAN.md + recipes + session export
- **Serve/vision/bridge:** `--serve` loop + systemd unit (desktop, CI-validated), image_describe (vision key pe), `--telegram` phone bridge (channels/ gateway — discord/whatsapp pattern ready), `/voice` (Termux:API mic)
```bash
kaal --telegram   # phone se task (config/telegram.json me token+ids)
```
- **Platform:** Termux/Linux/macOS/Windows, storage quota + auto-clean, `--resume/--history`

## Structure
```
kaal/kaal/{__main__,agent,config_store,config_defaults,storage,platform_adapt,scheduler,
  tui/,models/{router,llm,ollama},skills/{files,code,browser},mcp/{registry,github},
  agents/{orchestrator,specialists},memory/{store,patterns}}
config/ install/ memory/ logs/
```

## Status
v0.1.1-dev — security batch in. Tests 46 pass + benchmark 12/12 (hermetic).
Verify: `kaal "file read README.md"`.
