#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
LAUNCHER="$APP_DIR/launchers/biscuit-linux.sh"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$DESKTOP_DIR/biscuit.desktop"

mkdir -p "$DESKTOP_DIR"
chmod +x "$LAUNCHER"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Biscuit
Comment=Biscuit dictation toolbar
Exec=$LAUNCHER
Terminal=false
Categories=Utility;Accessibility;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"
echo "Biscuit desktop entry installed: $DESKTOP_FILE"
