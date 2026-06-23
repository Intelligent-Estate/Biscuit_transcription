#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
  LINK_DIR="$(cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
  SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
  [[ "$SCRIPT_PATH" != /* ]] && SCRIPT_PATH="$LINK_DIR/$SCRIPT_PATH"
done

APP_DIR="$(cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"

cd "$APP_DIR"
export PYTHONPATH="$APP_DIR/src"
python3 -m biscuit
