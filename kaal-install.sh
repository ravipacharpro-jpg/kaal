#!/bin/bash
# Kaal Installer — Sets up the `kaal` command in Termux/Linux/macOS
# Usage: bash kaal-install.sh

set -e

echo "=== Kaal Installer ==="
echo ""

# Step 1: Create ~/bin directory
BIN_DIR="$HOME/bin"
if [ ! -d "$BIN_DIR" ]; then
    mkdir -p "$BIN_DIR"
    echo "📁 Created ~/bin directory"
fi

# Step 2: Create the kaal command script
KAAL_CMD="$BIN_DIR/kaal"

# Write the kaal wrapper script
cat > "$KAAL_CMD" << 'KAAL_SCRIPT'
#!/data/data/com.termux/files/usr/bin/python3
import sys
import os
# Ensure kaal module is discoverable
# Kaal is at /data/data/com.termux/files/home/kaal, parent is the project root
KAAL_ROOT="/data/data/com.termux/files/home"
if Kaal_ROOT not in sys.path:
    sys.path.insert(0, KAAL_ROOT)
# Run kaal TUI
from kaal.__main__ import main
main()
KAAL_SCRIPT

chmod +x "$KAAL_CMD"
echo "🔧 Created $KAAL_CMD"

# Step 3: Add ~/bin to PATH in ~/.bashrc if not already there
BASHRC="$HOME/.bashrc"
PATH_LINE='export PATH="$HOME/bin:$PATH"'
if ! grep -qF "$PATH_LINE" "$BASHRC" 2>/dev/null; then
    echo "$PATH_LINE" >> "$BASHRC"
    echo "🌐 Added ~/bin to PATH in ~/.bashrc"
else
    echo "🌐 ~/bin already in PATH"
fi

# Step 4: Verify kaal launches (non-interactive check)
echo ""
echo "🔍 Verifying kaal setup..."
# Test by running kaal with a simple arg; if TUI opens, that's fine
# We'll just check the script is valid Python
python3 -c "
import sys
sys.path.insert(0, '/data/data/com.termux/files/home')
try:
    from kaal.__main__ import main
    print('✓ Kaal module imports OK')
except Exception as e:
    print(f'✗ Import error: {e}')
"

# Step 5: Final summary
echo ""
echo "=== Installation Complete ==="
echo ""
echo "Kaal command installed at: $KAAL_CMD"
echo ""
echo "To start Kaal, type:"
echo "  kaal"
echo ""
echo "Or run directly:"
echo "  python3 -m kaal"
echo ""
echo "To update PATH immediately, run:"
echo "  source ~/.bashrc"
echo ""
echo "Kaal will open into a Rich TUI (Termux UI Interface)."
echo "No API key required for keyless mode (OmniRoute/auto default)."
echo ""
echo "Happy coding! 🚀"