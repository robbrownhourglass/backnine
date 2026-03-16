#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$HOME/Library/LaunchAgents"
LAUNCHD_DIR="$ROOT_DIR/launchd"

mkdir -p "$AGENT_DIR" "$ROOT_DIR/logs"

render_template() {
  local src="$1"
  local dest="$2"
  sed "s|__ROOT__|$ROOT_DIR|g" "$src" > "$dest"
}

install_agent() {
  local label="$1"
  local template_path="$2"
  local plist_path="$AGENT_DIR/$label.plist"

  render_template "$template_path" "$plist_path"

  if launchctl bootout "gui/$(id -u)/$label" >/dev/null 2>&1; then
    :
  fi

  launchctl bootstrap "gui/$(id -u)" "$plist_path"
  launchctl kickstart -k "gui/$(id -u)/$label" >/dev/null 2>&1 || true

  echo "Installed and loaded launch agent: $label"
  echo "Plist: $plist_path"
}

install_agent "com.backnine.web" "$LAUNCHD_DIR/com.backnine.web.plist.template"
install_agent "com.backnine.scraper" "$LAUNCHD_DIR/com.backnine.scraper.plist.template"

echo "Logs:"
echo "  $ROOT_DIR/logs/launchd-web.log"
echo "  $ROOT_DIR/logs/launchd-scraper.log"
