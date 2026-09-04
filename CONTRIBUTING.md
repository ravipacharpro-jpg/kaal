# Contributing to Kaal

## Quick start
```bash
git clone https://github.com/ravipacharpro-jpg/kaal.git
cd kaal
bash install/install.sh
pip install -r requirements-dev.txt   # pytest (K-05: runtime dep nahi, dev-only)
python3 -m pytest tests/ -q   # 100+ pass hone chahiye
```

## Rules (short)
- **Minimal diff:** sirf jo poocha wahi badlo, scope creep nahi.
- **Test karo:** har fix ke saath `pytest tests/ -q` green rakho; naya behavior ho to test add karo.
- **Secrets kabhi commit nahi:** `config/*.json` (vault, telegram, keys) git me nahi jata — sirf `.example.json` edit karo. Pre-commit secret-scan hai.
- **Permissions default-deny:** naya sensitive op ho to `config_defaults.py` me default `ask`/`deny` rakho, `allow` nahi.
- **Paths:** repo-root-anchored paths use karo — `kaal/*.py` se single `".."`, `kaal/*/*.py` se `"..", ".."`. `~/config` ya `/home` me kabhi likho mat.
- **Language:** user-visible Hindi (Hinglish) strings, code comments concise English/Hindi.
- **i18n:** naya TUI text `kaal/i18n.py` me `t("key")` se — `STRINGS` me hi/en/zh teeno do. Seedha hardcode mat karo.
- **Lazy loading:** brain ko poora tool-spec mat do — `ROLE_TOOLS` me role entry add karo taaki task-wise subset bane.

## PR
- Ek PR = ek logical change. Kya badla / kaise verify kiya / kya uncertain hai — likho.

## Naya skill add karna (core extensible design)
1. `kaal/skills/<name>.py` banao + `SKILL = {"name":..., "desc":..., "version":...}` rakho.
2. Optional: `"tools": [{name, desc, params, fn}]` (brain auto-merge), `"commands": [...]` (palette docs), `"on_task"` / `"on_result"` hooks.
3. Hooks fail-soft hone chahiye (exception = ignore). Koi hook kabhi crash nahi karega.
4. Test `tests/test_kaal.py` me add karo. `python3 -m pytest tests/ -q` green rakho.
5. Rules: code/identifiers English-only; comments kisi bhi language me. Secrets kabhi log/commit nahi.
