# Kaal — samay se aage

Fully autonomous AI agent — Termux / Linux / macOS / Windows.
Premium Rich TUI: Todo panel + 1-line live Hindi status, TUI me code dump nahi.

## Install
```bash
git clone https://github.com/ravipacharpro-jpg/kaal.git
cd kaal
bash install/install.sh
# phir: kaal  (ya python3 -m kaal)
```

## Use
```bash
kaal                                   # interactive TUI
kaal "file read README.md"             # direct task
kaal "github repo ravipacharpro-jpg/kaal check karo"
```

TUI commands: `/endpoints` `/budget` `/memory` `/agents` `/quit`

## Design
- **TUI (Rich):** Todo auto `○/→/✓`, fixed 1-line live `⚡ abhi file read kar raha hu`, summary only
- **Model router:** OmniRoute/auto default keyless + 20 free-tier endpoints, agent khud select/rotate karta hai; user unlimited API vault me add kar sakta hai (same provider multiple allowed)
- **Skills:** files (safe, delete pe permission), code sandbox (30s timeout), browser text fetch, GitHub MCP
- **Multi-agent:** coder / researcher / analyzer / github_specialist auto-assign
- **Economy:** 5000 token/day default, 80% pe auto/fast saver
- **Memory:** SQLite sessions, 30-din auto-cleanup

## Structure
```
kaal/kaal/{__main__,agent,config_defaults,tui/,models/,skills/,mcp/,agents/,memory/}
config/ install/ memory/ logs/
```

## Status
Phase-1/2/3 done. Phase-4 (installer + 20 endpoints + docs) in progress.
Real LLM HTTP calls Phase-5 me — abhi router selection + local skills live hai.
