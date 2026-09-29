#!/bin/bash
set -e

CLIENT_DIR=$(cd "$(dirname "$0")" && pwd)
PLIST_NAME="com.presstalk.client.plist"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"


if ! command -v uv &>/dev/null; then
    echo "UV not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

UV_PATH=$(which uv)
echo "uv:         $UV_PATH"
echo "client dir: $CLIENT_DIR"

echo "Installing dependencies..."
cd "$CLIENT_DIR" && "$UV_PATH" sync


sed \
    -e "s|{{UV_PATH}}|$UV_PATH|g" \
    -e "s|{{CLIENT_DIR}}|$CLIENT_DIR|g" \
    -e "s|{{HOME}}|$HOME|g" \
    "$CLIENT_DIR/$PLIST_NAME.template" > "$LAUNCH_AGENTS/$PLIST_NAME"

echo "Agent installed: $LAUNCH_AGENTS/$PLIST_NAME"

launchctl unload "$LAUNCH_AGENTS/$PLIST_NAME" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS/$PLIST_NAME"

echo ""
echo "PressTalk is running and will launch every time you log in."
echo ""
echo "Don't forget to allow permissions in System Settings → Privacy & Security:"
echo "  Accessibility → /opt/homebrew/bin/uv"
echo "  Microphone  → run it manually once: uv run client.py"