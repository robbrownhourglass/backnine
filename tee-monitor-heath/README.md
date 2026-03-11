# ⛳ Mountrath Tee Monitor

Continuously scrapes the BRS Golf tee sheet and serves a dashboard
you can view from your phone anywhere in the world.

---

## Current Access URL

As of **2026-03-08 10:59:24 UTC**, the live quick-tunnel URL is:

`https://downloadable-diana-cloudy-constructed.trycloudflare.com`

This works now, but quick-tunnel URLs are not permanent and will change after a tunnel restart.

---

## Quick Start

### 1. Copy this folder to your MacBook

Put it somewhere permanent, e.g. `~/tee-monitor/`

### 2. Edit your credentials

Open `config.py` and fill in:

```python
BRS_USERNAME = "your_email@example.com"
BRS_PASSWORD = "your_password"
```

### 3. Run setup (once)

```bash
bash setup.sh
```

This installs:
- `playwright` + Chromium (headless browser for scraping)
- `flask` (dashboard server)
- `cloudflared` (free Cloudflare Tunnel for remote access)

### 4. Start everything

```bash
bash start.sh
```

You'll see output like:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Dashboard live at:

    https://random-name.trycloudflare.com

  Open this on your phone from anywhere.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Open that URL on your phone. Done.

---

## How it works

```
MacBook
  ├── scraper.py       Playwright logs in, scrapes every 2 min
  │                    → saves rolling 5h of data to tee_data.json
  ├── app.py           Flask serves dashboard at localhost:5050
  └── cloudflared      Free tunnel → public HTTPS URL (no port forwarding needed)
```

- **No router config needed** — Cloudflare Tunnel punches out through your firewall
- **No account needed** — uses Cloudflare's free quick tunnels
- **Session persistence** — scraper re-logs in automatically if kicked out

---

## Keeping it running after reboot

To auto-start on login, add a launchd plist or simply put this in your shell profile:

```bash
# In ~/.zshrc or ~/.bash_profile
# (not recommended for always-on — use launchd instead)
```

For always-on via launchd, create `~/Library/LaunchAgents/com.tee-monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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

Then: `launchctl load ~/Library/LaunchAgents/com.tee-monitor.plist`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login fails | Check credentials in config.py; try logging in manually to see if site changed |
| Slots show as "raw_fallback" | BRS updated their HTML — run scraper once, check logs/scraper.log, and update selectors in `scraper.py` `parse_tee_sheet()` |
| Tunnel URL not appearing | Check `logs/tunnel.log`; cloudflared may need a moment |
| Dashboard blank | Check `logs/dashboard.log` and `logs/scraper.log` |

---

## Resilience Plan (For Later)

Current mode:
- Uses Cloudflare quick tunnel (`*.trycloudflare.com`)
- `launchd` keeps processes running and auto-restarts on failure
- URL identity is not resilient: if tunnel restarts, URL can change

Upgrade path for resilient access:
- Move to a named Cloudflare Tunnel with a fixed subdomain (for example `tee.attuned.ie`)
- Keep WordPress on `attuned.ie` and use only a subdomain for this app
- Keep host awake (disable sleep), prefer wired network where possible
- Use a UPS for brief power outages

Quick way to find the current URL from logs:

```bash
grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' logs/tunnel.log | tail -1
```

---

## Files

| File | Purpose |
|------|---------|
| `config.py` | Credentials & settings |
| `scraper.py` | Playwright scraper loop |
| `app.py` | Flask dashboard |
| `setup.sh` | One-time install |
| `start.sh` | Launches everything |
| `tee_data.json` | Live data store (auto-created) |
| `logs/` | Per-process logs |

---

## Deploy On SSH Server (Static URL)

Use this when the project is on GitHub and you want it always available from your phone.

### 1. SSH in and clone from GitHub

```bash
ssh youruser@your-server
git clone https://github.com/YOUR_USER/tee-monitor.git
cd tee-monitor
```

### 2. Configure credentials

Edit `config.py`:

```python
BRS_USERNAME = "your_email@example.com"
BRS_PASSWORD = "your_password"
```

### 3. Install dependencies on server

```bash
bash setup.sh
```

If `setup.sh` cannot install `cloudflared` automatically on Linux, install it manually:

```bash
# Debian/Ubuntu example
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared
```

### 4. Run scraper + web as systemd services

Create service files:

```bash
sudo tee /etc/systemd/system/tee-monitor-scraper.service >/dev/null <<'EOF'
[Unit]
Description=Tee Monitor Scraper
After=network.target

[Service]
Type=simple
User=YOUR_SERVER_USER
WorkingDirectory=/home/YOUR_SERVER_USER/tee-monitor
ExecStart=/usr/bin/python3 scraper.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/tee-monitor-web.service >/dev/null <<'EOF'
[Unit]
Description=Tee Monitor Flask Dashboard
After=network.target

[Service]
Type=simple
User=YOUR_SERVER_USER
WorkingDirectory=/home/YOUR_SERVER_USER/tee-monitor
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Enable/start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tee-monitor-scraper tee-monitor-web
sudo systemctl status tee-monitor-scraper tee-monitor-web --no-pager
```

### 5. Set up named Cloudflare Tunnel (stable URL)

Prereq: domain in Cloudflare (for example `golf.yourdomain.com`).

```bash
cloudflared tunnel login
cloudflared tunnel create tee-monitor
cloudflared tunnel route dns tee-monitor golf.yourdomain.com
```

Create tunnel config:

```bash
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<'EOF'
tunnel: tee-monitor
credentials-file: /home/YOUR_SERVER_USER/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: golf.yourdomain.com
    service: http://localhost:5050
  - service: http_status:404
EOF
```

Install/start tunnel as service:

```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
sudo systemctl status cloudflared --no-pager
```

You now have a stable URL:

`https://golf.yourdomain.com`

### Useful ops commands

```bash
# app services
sudo systemctl restart tee-monitor-scraper tee-monitor-web
sudo journalctl -u tee-monitor-scraper -f
sudo journalctl -u tee-monitor-web -f

# tunnel
sudo systemctl restart cloudflared
sudo journalctl -u cloudflared -f
```
