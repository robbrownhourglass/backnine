#!/bin/bash
# start.sh — Launch the unified Back Nine app, all scrapers, and one Cloudflare tunnel.

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

PORT="${PORT:-5080}"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"
CLOUDFLARED_BIN="$(command -v cloudflared || true)"

if [ -z "$CLOUDFLARED_BIN" ]; then
  if [ -x "$DIR/tee-monitor-heath/bin/cloudflared" ]; then
    CLOUDFLARED_BIN="$DIR/tee-monitor-heath/bin/cloudflared"
  elif [ -x "$DIR/tee-monitor-athenry/bin/cloudflared" ]; then
    CLOUDFLARED_BIN="$DIR/tee-monitor-athenry/bin/cloudflared"
  elif [ -x "$DIR/tee-monitor-mountrath/bin/cloudflared" ]; then
    CLOUDFLARED_BIN="$DIR/tee-monitor-mountrath/bin/cloudflared"
  fi
fi

if [ -z "$CLOUDFLARED_BIN" ]; then
  echo "cloudflared not found."
  exit 1
fi

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$SCRAPE_HEATH_PID" "$SCRAPE_ATHENRY_PID" "$SCRAPE_MOUNTRATH_PID" "$WEB_PID" "$TUNNEL_PID" "$MONITOR_PID" 2>/dev/null || true
  echo "Stopped."
  exit 0
}
trap cleanup INT TERM

start_tunnel() {
  "$CLOUDFLARED_BIN" tunnel --url "http://localhost:$PORT" > "$LOG_DIR/tunnel.log" 2>&1 &
  TUNNEL_PID=$!
  echo "  PID: $TUNNEL_PID | Log: logs/tunnel.log"
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Back Nine — Starting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "▶ Starting scrapers..."
"$PYTHON_BIN" -u manage.py scrape the-heath > "$LOG_DIR/scraper-the-heath.log" 2>&1 &
SCRAPE_HEATH_PID=$!
echo "  the-heath:  $SCRAPE_HEATH_PID | logs/scraper-the-heath.log"

"$PYTHON_BIN" -u manage.py scrape athenry > "$LOG_DIR/scraper-athenry.log" 2>&1 &
SCRAPE_ATHENRY_PID=$!
echo "  athenry:    $SCRAPE_ATHENRY_PID | logs/scraper-athenry.log"

"$PYTHON_BIN" -u manage.py scrape mountrath > "$LOG_DIR/scraper-mountrath.log" 2>&1 &
SCRAPE_MOUNTRATH_PID=$!
echo "  mountrath:  $SCRAPE_MOUNTRATH_PID | logs/scraper-mountrath.log"

echo ""
echo "▶ Starting unified web app on port $PORT..."
"$PYTHON_BIN" -u manage.py serve --port "$PORT" > "$LOG_DIR/web.log" 2>&1 &
WEB_PID=$!
echo "  web:        $WEB_PID | logs/web.log"

sleep 2

echo ""
echo "▶ Starting Cloudflare Tunnel..."
start_tunnel

echo ""
echo "  Waiting for public URL..."
for i in $(seq 1 20); do
  URL=$(grep -oE 'https://[a-z0-9\-]+\.trycloudflare\.com' "$LOG_DIR/tunnel.log" 2>/dev/null | head -1)
  if [ -n "$URL" ]; then
    break
  fi
  sleep 1
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -n "$URL" ]; then
  echo "  Dashboard live at:"
  echo ""
  echo "    $URL"
  echo ""
  echo "  Club routes:"
  echo "    $URL/the-heath/"
  echo "    $URL/athenry/"
  echo "    $URL/mountrath/"
else
  echo "  Tunnel URL not found yet."
  echo "  Check logs/tunnel.log."
fi
echo ""
echo "  Local: http://localhost:$PORT"
echo "  Logs:  ./logs/"
echo ""
echo "  Press Ctrl+C to stop everything."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

(
  while true; do
    if ! kill -0 "$SCRAPE_HEATH_PID" 2>/dev/null; then
      echo "the-heath scraper exited."
      exit 1
    fi
    if ! kill -0 "$SCRAPE_ATHENRY_PID" 2>/dev/null; then
      echo "athenry scraper exited."
      exit 1
    fi
    if ! kill -0 "$SCRAPE_MOUNTRATH_PID" 2>/dev/null; then
      echo "mountrath scraper exited."
      exit 1
    fi
    if ! kill -0 "$WEB_PID" 2>/dev/null; then
      echo "web app exited."
      exit 1
    fi
    if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
      echo "tunnel exited, restarting..."
      start_tunnel
    fi
    sleep 5
  done
) &
MONITOR_PID=$!

wait "$MONITOR_PID"
