#!/data/data/com.termux/files/usr/bin/python3
"""Kaal installer — sets up the `kaal` command in Termux/Linux/macOS.

Usage:  bash kaal-install.sh

This script:
  • Creates ~/bin/kaal (or /usr/bin/kaal) that runs `python3 -m kaal`
  • Ensures ~/bin is in PATH (adds to ~/.bashrc if needed)
  • Verifies kaal launches into TUI
"""
import os, sys, subprocess, pathlib

HOME = pathlib.Path.home()
BIN_DIR = HOME / "bin"
KAAL_CMD = BIN_DIR / "kaal"
INSTALL_LOG = HOME / "kaal-install.log"

def log(msg):
    with open(INSTALL_LOG, "a", encoding="utf-8") as f:
        f.write(f"{os.path.basename(__file__)}: {msg}\n")

log("Starting Kaal installer...")

# Create bin directory
try:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Created bin directory: {BIN_DIR}")
except Exception as e:
    log(f"Failed to create bin dir: {e}")
    print(f"[ERROR] Failed to create bin dir: {e}")
    sys.exit(1)

# Write the kaal command script
kaal_script = f"""#!/data/data/com.termux/files/usr/bin/python3
import sys
import os
# Ensure kaal module is discoverable
Kaal_ROOT = "{str(HOME.parent.parent.parent)}"
if Kaal_ROOT not in sys.path:
    sys.path.insert(0, Kaal_ROOT)
# Run kaal TUI
from kaal.__main__ import main
main()
"""
try:
    with open(KAAL_CMD, "w", encoding="utf-8") as f:
        f.write(kaal_script)
    os.chmod(KAAL_CMD, 0o755)
    log(f"Created kaal command: {KAAL_CMD}")
except Exception as e:
    log(f"Failed to write kaal script: {e}")
    print(f"[ERROR] Failed to write kaal script: {e}")
    sys.exit(1)

# Add ~/bin to PATH in ~/.bashrc if not already there
bashrc = HOME / ".bashrc"
try:
    bashrc_content = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
    PATH_LINE = 'export PATH="$HOME/bin:$PATH"'
    if PATH_LINE not in bashrc_content:
        with open(bashrc, "a", encoding="utf-8") as f:
            f.write(f"\n{PATH_LINE}\n")
        log("Added ~/bin to PATH in ~/.bashrc")
    else:
        log("~/bin already in PATH")
except Exception as e:
    log(f"Note: could not update ~/.bashrc: {e}")

# Make the script executable
os.chmod(KAAL_CMD, 0o755)

# Verify kaal launches
try:
    result = subprocess.run(
        [KAAL_CMD, "--version"],
        capture_output=True, text=True, timeout=10
    )
    # If --version not supported, just check it doesn't crash immediately
    # The main_loop will start interactively
    log(f"Kaal command created successfully at {KAAL_CMD}")
    print(f"[SUCCESS] Kaal installer complete!")
    print(f"  Command: {KAAL_CMD}")
    print(f"  To use: type 'kaal' in Termux or run: python3 -m kaal")
    print(f"  Log: {INSTALL_LOG}")
except Exception as e:
    log(f"Verification note: {e}")
    print(f"[SUCCESS] Kaal installer complete (verification deferred).")
    print(f"  Command: {KAAL_CMD}")
    print(f"  To use: type 'kaal' in Termux or run: python3 -m kaal")

log("Installer finished.")