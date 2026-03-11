# ⛳ Mountrath Tee Monitor — Summary

A self-hosted tool that continuously scrapes the BRS Golf tee sheet and serves a live dashboard viewable from your phone anywhere in the world.

---

## Current access URL

As of **2026-03-08 10:59:24 UTC**, the live quick-tunnel URL is:

`https://downloadable-diana-cloudy-constructed.trycloudflare.com`

This URL is valid now, but quick-tunnel URLs are not fixed and can change after restart.

---

## What it does

- Logs into `members.brsgolf.com/mountrath` using Playwright (headless browser)
- Scrapes tee time slots every 2 minutes
- Keeps a rolling 5-hour history of snapshots in a local JSON file
- Serves a mobile-friendly dashboard on your MacBook
- Exposes the dashboard publicly via a free Cloudflare Tunnel — no port forwarding, no domain, no account needed

---

## Project files

| File | Purpose |
|------|---------|
| `config.py` | Your BRS login credentials and settings |
| `scraper.py` | Playwright scraper loop — logs in, scrapes, saves data |
| `app.py` | Flask web dashboard |
| `setup.sh` | One-time dependency installer |
| `start.sh` | Launches scraper + dashboard + tunnel together |
| `tee_data.json` | Auto-created live data store |
| `logs/` | Per-process log files |

---

## First-time setup

### 1. Place the folder somewhere permanent

```bash
# e.g. your home directory
mv tee-monitor ~/tee-monitor
```

### 2. Add your BRS credentials

Edit `config.py`:

```python
BRS_USERNAME = "your_email@example.com"
BRS_PASSWORD = "your_password"
```

### 3. Run setup (once only)

```bash
bash ~/tee-monitor/setup.sh
```

This installs:
- `playwright` + Chromium (headless browser)
- `flask` (dashboard server)
- `cloudflared` (Cloudflare Tunnel CLI, via Homebrew if available)

---

## Running it

```bash
bash ~/tee-monitor/start.sh
```

On startup you'll see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Dashboard live at:

    https://some-random-name.trycloudflare.com

  Open this on your phone from anywhere.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Open that URL on your phone — it works on any network, anywhere. Press `Ctrl+C` to stop everything cleanly.

Local dashboard is also at: `http://localhost:5050`

---

## Auto-start on boot (optional)

To keep it running permanently on your MacBook server, create a launchd agent.

Create the file `~/Library/LaunchAgents/com.tee-monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.tee-monitor</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/YOUR_USERNAME/tee-monitor/start.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/Users/YOUR_USERNAME/tee-monitor/logs/launchd.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/YOUR_USERNAME/tee-monitor/logs/launchd.log</string>
</dict>
</plist>
```

Replace `YOUR_USERNAME` with your Mac username (run `whoami` if unsure), then load it:

```bash
launchctl load ~/Library/LaunchAgents/com.tee-monitor.plist
```

To stop it: `launchctl unload ~/Library/LaunchAgents/com.tee-monitor.plist`

> **Note:** The Cloudflare Tunnel URL changes every time the process restarts. If you need a stable URL, create a free Cloudflare account and set up a named tunnel — but for casual use the random URL is fine.

---

## Troubleshooting

| Symptom | Likely cause & fix |
|---------|--------------------|
| Login fails immediately | Wrong credentials in `config.py`, or BRS changed their login page layout |
| Dashboard shows "raw_fallback" text | BRS HTML structure didn't match expected selectors — share a snippet from `logs/scraper.log` to get updated selectors |
| No tunnel URL appears | Check `logs/tunnel.log`; `cloudflared` may need 10–15 seconds on slow connections |
| Dashboard loads but shows no data | Scraper may still be on its first run — wait one interval (2 min) and refresh |
| Mac goes to sleep | Go to System Settings → Battery → disable "Put hard disks to sleep" and enable "Prevent automatic sleeping when display is off" |

---

## Resilience plan (later upgrade)

Current state:
- `launchd` runs the stack in background and restarts if processes die
- Tunnel currently uses Cloudflare quick tunnel (`*.trycloudflare.com`)
- URL is not guaranteed to stay the same after restart

Recommended resilient target:
- Named Cloudflare Tunnel + fixed subdomain (example `tee.attuned.ie`)
- Keep WordPress on `attuned.ie`/`www.attuned.ie`; this app on subdomain only
- Keep server awake, prefer wired network, and use UPS for outage tolerance

Find latest quick URL from logs:

```bash
grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' logs/tunnel.log | tail -1
```

---

## Adjusting settings

All key settings are in `config.py`:

```python
SCRAPE_INTERVAL = 120   # seconds between scrapes
HISTORY_HOURS   = 5     # how many hours of snapshots to keep
DASHBOARD_PORT  = 5050  # local port for the Flask dashboard
```

---

## Deploying on an SSH Server (Stable URL)

If this repo is on GitHub and you want a permanent phone URL:

1. SSH to server and clone:

```bash
ssh youruser@your-server
git clone https://github.com/YOUR_USER/tee-monitor.git
cd tee-monitor
```

2. Set credentials in `config.py` (`BRS_USERNAME`, `BRS_PASSWORD`).

3. Install dependencies:

```bash
bash setup.sh
```

4. Run scraper and dashboard as `systemd` services (recommended), not with `start.sh`.

Create:
- `/etc/systemd/system/tee-monitor-scraper.service`
- `/etc/systemd/system/tee-monitor-web.service`

Use `WorkingDirectory=/home/YOUR_SERVER_USER/tee-monitor` and:
- scraper `ExecStart=/usr/bin/python3 scraper.py`
- web `ExecStart=/usr/bin/python3 app.py`

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tee-monitor-scraper tee-monitor-web
```

5. Use a **named Cloudflare Tunnel** for a static hostname:

```bash
cloudflared tunnel login
cloudflared tunnel create tee-monitor
cloudflared tunnel route dns tee-monitor golf.yourdomain.com
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: tee-monitor
credentials-file: /home/YOUR_SERVER_USER/.cloudflared/<TUNNEL_ID>.json
ingress:
  - hostname: golf.yourdomain.com
    service: http://localhost:5050
  - service: http_status:404
```

Then install/start cloudflared service:

```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

After this, your stable URL is:

`https://golf.yourdomain.com`
