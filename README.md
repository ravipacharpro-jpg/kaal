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
- **Brain 2 modes:** vault API key ho YA Ollama local chal raha ho to LLM tool-loop (10 tools + personas + self-correction); nahi to keyword rule path (fast, par AI nahi — seedha likha hai)
- **Endpoints:** 20 configured targets; bina key wale call nahi hote (sirf list) — key `/key` se add karo ya Ollama chalao. `ollama_local` hi real keyless hai.
- **Routing:** keyword classify + specialist personas; reasoning LLM karta hai, router nahi
- **Sandbox:** AST-verified (import/open/eval/dunder block) + optional docker (PC). OS-level boundary nahi — sensitive machine pe `/perm` tight rakho.
- **Skills:** files (backup+undo+checkpoints), code, browser (Playwright/HTTP), GitHub, git (commit/changelog), bash allowlist
- **Multi-agent:** 5 personas, desktop pe parallel, Termux pe sequential
- **Economy:** daily budget, 80% pe saver mode, per-endpoint tracking
- **Memory:** SQLite + patterns + PLAN.md + recipes + session export
- **Platform:** Termux/Linux/macOS/Windows, storage quota + auto-clean, `--resume/--history`

## Structure
```
kaal/kaal/{__main__,agent,config_store,config_defaults,storage,platform_adapt,scheduler,
  tui/,models/{router,llm,ollama},skills/{files,code,browser},mcp/{registry,github},
  agents/{orchestrator,specialists},memory/{store,patterns}}
config/ install/ memory/ logs/
```

## Status
v0.1.1-dev — diagnose fixes in. Tests: `python3 -m unittest discover tests` (24 pass, HOME/cwd-independent, CI on 3 OS).
Verify: `kaal "file read README.md"`.
