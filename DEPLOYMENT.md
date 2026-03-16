# Deployment

## What this stack does

This repo now includes two deployment paths:

- `web` runs the unified Back Nine app with Gunicorn
- `scraper` runs the long-lived Playwright scraping loop
- `caddy` terminates HTTPS and reverse-proxies to the web app

Files:

- `Dockerfile`
- `docker-compose.yml`
- `Caddyfile`
- `.env.example`
- `install_backnine_launch_agents.sh`
- `launchd/com.backnine.web.plist.template`
- `launchd/com.backnine.scraper.plist.template`

## Recommendation

The cleanest production path is a Linux VPS or Linux VM, not a Mac on a home network.

This stack will still work on a home machine if all of these are true:

1. your domain points to your public IP
2. ports `80` and `443` are forwarded from your router to this machine
3. the machine stays awake
4. Docker stays running

If those are not true, automatic public HTTPS will not complete.

## HTTPS

The `caddy` service handles HTTPS automatically.

You do not need to manually provision certificates if:

1. the domain in `.env` is correct
2. that domain resolves publicly to the server
3. inbound `80` and `443` are reachable

## Secrets

Club credentials normally live in:

```text
secrets/clubs.local.json
```

For hosted platforms without a local secret file, set:

```bash
SECRET_CONFIG_JSON={"clubs":{"the-heath":{"brs_username":"...","brs_password":"..."},"athenry":{"brs_username":"...","brs_password":"..."},"mountrath":{"brs_username":"...","brs_password":"..."}}}
```

The app reads secrets in this order:

1. `SECRET_CONFIG_JSON`
2. `/etc/secrets/clubs.local.json`
3. `secrets/clubs.local.json`

## macOS Home-Server Setup

This is the current live setup on the Mac server:

- `caddy` runs as a Homebrew service
- `gunicorn` runs as `com.backnine.web`
- `python manage.py scrape-all` runs as `com.backnine.scraper`

### Caddy

Install and run Caddy with Homebrew:

```bash
brew install caddy
brew services start caddy
```

The live `/usr/local/etc/Caddyfile` is currently shaped like:

```caddy
backnine.ie {
    redir https://www.backnine.ie{uri} permanent
}

www.backnine.ie {
    reverse_proxy 127.0.0.1:5080
}
```

### DNS

For a home connection with a changing public IP, use a FRITZ!Box `MyFRITZ!` hostname and point the domain at it:

- `@ ALIAS <your-box>.myfritz.net`
- `www CNAME <your-box>.myfritz.net`

That allows the FRITZ!Box to keep the public address updated automatically.

### Launchd

Install the persistent Back Nine jobs:

```bash
./install_backnine_launch_agents.sh
```

That creates and loads:

- `com.backnine.web`
- `com.backnine.scraper`

Useful checks:

```bash
launchctl list | rg 'com.backnine|homebrew.mxcl.caddy'
```

```bash
tail -f logs/launchd-web.log
tail -f logs/launchd-scraper.log
```

### Behavior

- `manage.py serve` performs one immediate scrape before starting the web app
- `manage.py scrape-all` then keeps all clubs updating every `600` seconds (`10` minutes)
- the web app serves stored data only; it does not scrape on page refresh

## Docker Setup

1. Copy the example env file:

```bash
cp .env.example .env
```

2. Set your real domain in `.env`:

```bash
DOMAIN=your-real-domain.example.com
```

3. Render secret files also work. If you upload a secret file named:

```text
clubs.local.json
```

the app will read it from:

```text
/etc/secrets/clubs.local.json
```

4. Start the stack:

```bash
docker compose up -d --build
```

5. Check logs:

```bash
docker compose logs -f web
docker compose logs -f scraper
docker compose logs -f caddy
```

## Updating

```bash
docker compose up -d --build
```

## Stopping

```bash
docker compose down
```

## Notes

- The app is currently Flask-based, not Django-based.
- When you later move to Django, the same shape still works: app container, scraper/worker container, reverse proxy with HTTPS.
- Data persists in `./data`, and secrets stay outside the image in `./secrets`.
