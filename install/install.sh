#!/bin/bash
# Kaal installer — Termux/Linux/macOS/Windows-gitbash
set -e
cd "$(dirname "$0")"
pip install -r requirements.txt -q
echo "✅ Kaal ready — chalao: python3 -m kaal"
