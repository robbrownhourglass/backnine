# Back Nine

Back Nine is a multi-club tee monitor built with Flask and Playwright.

Current clubs:

- The Heath
- Athenry
- Mountrath

## Local run

```bash
python3 manage.py serve --port 5080
```

Open:

- `http://127.0.0.1:5080/`

`serve` performs one immediate scrape for all clubs before starting the web app.

## Scraper

Run all club scrapers:

```bash
python3 manage.py scrape-all
```

This keeps all three clubs updated on a `10` minute cycle using the per-club `scrape_interval` in [`config/clubs.json`](./config/clubs.json).

## Secrets

Club credentials live in:

- `secrets/clubs.local.json`

That file is intentionally gitignored.

## Deployment

See:

- `DEPLOYMENT.md`
- `render.yaml`

## macOS home-server setup

The current live macOS setup uses:

- `caddy` on ports `80` and `443`
- `gunicorn` on `127.0.0.1:5080`
- `launchd` for the persistent web and scraper jobs

Install the Back Nine launch agents with:

```bash
./install_backnine_launch_agents.sh
```

That installs:

- `com.backnine.web`
- `com.backnine.scraper`

Templates for those agents live in:

- `launchd/com.backnine.web.plist.template`
- `launchd/com.backnine.scraper.plist.template`
