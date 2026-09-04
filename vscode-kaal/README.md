# Kaal VS Code Extension (scaffold, v0.1.0)

Bridge to the Kaal agent via `kaal --mode rpc` (JSON-RPC over stdio).

## Use (PC: Linux/macOS/Windows, VS Code 1.85+)
1. Install Kaal: `git clone https://github.com/ravipacharpro-jpg/kaal.git && bash kaal/install/install.sh`
2. Ensure `kaal` is on PATH (or set `kaal.bin` setting to full path).
3. Copy this folder, `npm install` (needs `vscode` module via `@vscode/vsce`), F5 to debug.
4. Commands: **Kaal: Run Task**, **Kaal: Review Active File**.

## Honest notes
- Untested scaffold — needs a contributor with VS Code dev setup to verify.
- Methods used: `initialize`, `prompt/run` (see `kaal/rpc.py` for the full subset).
- Termux pe VS Code nahi chalta — ye sirf PC ke liye hai.
