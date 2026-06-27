#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
LAUNCHER="$APP_DIR/Biscuit-macOS.command"
BUNDLE="$HOME/Applications/Biscuit.app"
MACOS_DIR="$BUNDLE/Contents/MacOS"
RESOURCES_DIR="$BUNDLE/Contents/Resources"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"
chmod +x "$LAUNCHER"

export PYTHONPATH="$APP_DIR/src"
echo "Fetching Biscuit speech model from Systran/faster-whisper-tiny.en..."
python -m pip install --upgrade -r "$APP_DIR/requirements.txt"
python "$APP_DIR/scripts/prefetch_model.py"

cat > "$MACOS_DIR/Biscuit" <<EOF
#!/usr/bin/env bash
exec "$LAUNCHER"
EOF
chmod +x "$MACOS_DIR/Biscuit"

cat > "$BUNDLE/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>Biscuit</string>
  <key>CFBundleDisplayName</key>
  <string>Biscuit</string>
  <key>CFBundleExecutable</key>
  <string>Biscuit</string>
  <key>CFBundleIdentifier</key>
  <string>local.cenedril.biscuit</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
</dict>
</plist>
EOF

echo "Biscuit.app installed: $BUNDLE"
