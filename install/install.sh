#!/bin/bash
# Kaal installer — Termux / Linux / macOS / Windows-gitbash
# Usage: bash install/install.sh  (repo root se: bash install/install.sh)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "🤖 Kaal install — Ahead of Time"
python3 --version || { echo "❌ python3 chahiye"; exit 1; }

# Termux detect: pkg available?
if command -v pkg >/dev/null 2>&1; then
  echo "📱 Termux detect — python ok"
fi

pip install -r requirements.txt -q && echo "📦 deps ok"

# `kaal` wrapper PATH me (user bin)
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
BASH_PATH="$(command -v bash)"
cat > "$BIN_DIR/kaal" <<EOF
#!$BASH_PATH
cd "$ROOT" || exit 1
exec python3 -m kaal "\$@"
EOF
chmod +x "$BIN_DIR/kaal"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "➕ PATH me add karo: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

echo "✅ Kaal ready — chalao: kaal  OR  python3 -m kaal"
echo "   Commands: /endpoints /budget /memory /agents /quit"
