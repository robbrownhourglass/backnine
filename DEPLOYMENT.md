# Deployment

## What this stack does

This repo now includes a simple production deployment path:

- `web` runs the unified Back Nine app with Gunicorn
- `scraper` runs the long-lived Playwright scraping loop
- `caddy` terminates HTTPS and reverse-proxies to the web app

Files:

- `Dockerfile`
- `docker-compose.yml`
- `Caddyfile`
- `.env.example`

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

## Setup

1. Copy the example env file:

```bash
cp .env.example .env
```

2. Set your real domain in `.env`:

```bash
DOMAIN=your-real-domain.example.com
```

3. Make sure `secrets/clubs.local.json` contains the club credentials.

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
