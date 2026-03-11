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

## Scraper

Run all club scrapers:

```bash
python3 manage.py scrape-all
```

## Secrets

Club credentials live in:

- `secrets/clubs.local.json`

That file is intentionally gitignored.

## Deployment

See:

- `DEPLOYMENT.md`
- `render.yaml`
