#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.tee-monitor-heath"
AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$AGENT_DIR/$LABEL.plist"
LOG_PATH="$DIR/logs/launchd-heath.log"

mkdir -p "$AGENT_DIR" "$DIR/logs"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$DIR/start.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>$DIR/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_PATH</string>
  <key>StandardErrorPath</key>
  <string>$LOG_PATH</string>
</dict>
</plist>
PLIST

if launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  :
fi

if launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1; then
  launchctl kickstart -k "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
else
  launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
  launchctl load "$PLIST_PATH"
fi

echo "Installed and loaded launch agent: $LABEL"
echo "Plist: $PLIST_PATH"
echo "Log:   $LOG_PATH"
