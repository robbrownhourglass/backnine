#!/bin/bash
# setup.sh — Install all dependencies for the Mountrath Tee Monitor
# Run once before first launch.

set -e
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Mountrath Tee Monitor — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "✗ Python 3 not found. Install it from https://python.org"
  exit 1
fi

echo "✓ Python: $(python3 --version)"

# Install Python deps
echo ""
echo "Installing Python packages..."
pip3 install playwright flask --break-system-packages 2>/dev/null || \
  pip3 install playwright flask

echo ""
echo "Installing Playwright browsers..."
python3 -m playwright install chromium

# Install Cloudflare tunnel (cloudflared) if not present
if ! command -v cloudflared &>/dev/null; then
  echo ""
  echo "Installing cloudflared (Cloudflare Tunnel)..."

  ARCH=$(uname -m)
  OS=$(uname -s | tr '[:upper:]' '[:lower:]')

  if [ "$OS" = "darwin" ]; then
    if command -v brew &>/dev/null; then
      brew install cloudflare/cloudflare/cloudflared
    else
      echo "  Homebrew not found. Downloading cloudflared manually..."
      if [ "$ARCH" = "arm64" ]; then
        URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
      else
        URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
      fi
      curl -L "$URL" -o /tmp/cloudflared.tgz
      tar -xzf /tmp/cloudflared.tgz -C /tmp
      mv /tmp/cloudflared /usr/local/bin/cloudflared
      chmod +x /usr/local/bin/cloudflared
    fi
  else
    echo "  Please install cloudflared manually: https://developers.cloudflare.com/cloudflared/install"
  fi
else
  echo "✓ cloudflared already installed: $(cloudflared --version 2>&1 | head -1)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit config.py with your BRS login credentials"
echo "  2. Run: bash start.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
