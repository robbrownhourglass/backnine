#!/bin/bash
# start.sh — Launch scraper, dashboard, and Cloudflare tunnel together.
# Stop everything cleanly with Ctrl+C.

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

PORT=5050
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"
CLOUDFLARED_BIN="$DIR/bin/cloudflared"

if [ ! -x "$CLOUDFLARED_BIN" ]; then
  CLOUDFLARED_BIN="$(command -v cloudflared || true)"
fi

if [ -z "$CLOUDFLARED_BIN" ]; then
  echo "✗ cloudflared not found."
  echo "  Install it with: bash setup.sh"
  echo "  Or place binary at: $DIR/bin/cloudflared"
  exit 1
fi

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$SCRAPER_PID" "$FLASK_PID" "$TUNNEL_PID" "$MONITOR_PID" 2>/dev/null || true
  echo "Stopped."
  exit 0
}
trap cleanup INT TERM

start_tunnel() {
  "$CLOUDFLARED_BIN" tunnel --url http://localhost:$PORT > "$LOG_DIR/tunnel.log" 2>&1 &
  TUNNEL_PID=$!
  echo "  PID: $TUNNEL_PID  |  Log: logs/tunnel.log"
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Mountrath Tee Monitor — Starting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Start scraper
echo "▶ Starting scraper..."
python3 scraper.py > "$LOG_DIR/scraper.log" 2>&1 &
SCRAPER_PID=$!
echo "  PID: $SCRAPER_PID  |  Log: logs/scraper.log"

# 2. Start Flask dashboard
echo ""
echo "▶ Starting dashboard on port $PORT..."
python3 app.py > "$LOG_DIR/dashboard.log" 2>&1 &
FLASK_PID=$!
echo "  PID: $FLASK_PID  |  Log: logs/dashboard.log"

# Give Flask a moment to start
sleep 2

# 3. Start Cloudflare Tunnel (no login needed — quick tunnel)
echo ""
echo "▶ Starting Cloudflare Tunnel..."
start_tunnel

# Wait for tunnel URL to appear in logs
echo ""
echo "  Waiting for public URL..."
for i in $(seq 1 20); do
  URL=$(grep -oP 'https://[a-z0-9\-]+\.trycloudflare\.com' "$LOG_DIR/tunnel.log" 2>/dev/null | head -1)
  if [ -n "$URL" ]; then
    break
  fi
  sleep 1
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -n "$URL" ]; then
  echo "  ✓ Dashboard live at:"
  echo ""
  echo "    $URL"
  echo ""
  echo "  Open this on your phone from anywhere."
else
  echo "  ⚠  Tunnel URL not found yet."
  echo "  Check logs/tunnel.log for the URL."
fi
echo ""
echo "  Local:  http://localhost:$PORT"
echo "  Logs:   ./logs/"
echo ""
echo "  Press Ctrl+C to stop everything."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Keep alive and restart tunnel if it exits
(
  while true; do
    if ! kill -0 "$SCRAPER_PID" 2>/dev/null; then
      echo "✗ Scraper process exited. Stopping monitor."
      exit 1
    fi
    if ! kill -0 "$FLASK_PID" 2>/dev/null; then
      echo "✗ Dashboard process exited. Stopping monitor."
      exit 1
    fi
    if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
      echo "⚠ Tunnel process exited. Restarting..."
      start_tunnel
    fi
    sleep 5
  done
) &
MONITOR_PID=$!

wait "$MONITOR_PID"
