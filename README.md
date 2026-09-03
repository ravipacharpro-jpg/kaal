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

## Design
- **TUI (Rich):** Todo auto `○/→/✓` + agent column, fixed 1-line live `⚡ abhi file read kar raha hu`, summary only
- **Model router:** OmniRoute/auto default keyless + 20 free-tier endpoints, agent khud select/rotate karta hai; vault keys pe real LLM calls + fallback chain
- **Skills:** files (safe, delete pe permission), code sandbox (30s timeout), browser (Playwright MCP live, fallback light-fetch), GitHub MCP
- **Multi-agent:** coder / researcher / analyzer / github_specialist auto-assign
- **Economy:** config/economy.json se budget, 80% pe auto/fast saver, per-endpoint daily tracking
- **Memory:** SQLite sessions + pattern learning (similar task suggest), 30-din auto-cleanup
- **Platform:** auto-detect Termux/Linux/macOS/Windows, storage quota + startup auto-clean, session resume

## Structure
```
kaal/kaal/{__main__,agent,config_store,config_defaults,storage,platform_adapt,scheduler,
  tui/,models/{router,llm,ollama},skills/{files,code,browser},mcp/{registry,github},
  agents/{orchestrator,specialists},memory/{store,patterns}}
config/ install/ memory/ logs/
```

## Status
v0.1.0 — sab phases complete, verified on Termux.
