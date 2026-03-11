# Back Nine Multi-Club Architecture Plan

## Current State

The repo currently contains three near-identical single-club apps:

- `tee-monitor-heath`
- `tee-monitor-athenry`
- `tee-monitor-mountrath`

Each app has the same pattern:

- `scraper.py` logs into a club-specific BRS page with Playwright
- `tee_data.json` stores the rolling scrape history
- `app.py` serves one HTML dashboard plus `/api/data`
- `config.py` holds credentials, URLs, port, and scrape settings

The differences between clubs are small:

- club branding and title text
- hole pars / course geometry
- BRS login and tee-sheet URLs
- a few fallback parsing exceptions
- local port / launch scripts

That means the main problem is not three different products. It is one product copied three times.

## Recommendation

Use Django, but only for the web app and data model layer.

Do not start by rewriting everything into a full Django monolith in one step. Keep the scraper logic conceptually separate and move it into a shared service layer that Django can call or schedule.

Why Django is a good fit here:

- you want one hosted app with multiple club pages such as `/the-heath` and `/round-draft`
- you will likely need admin screens for clubs, credentials, feature flags, pars, branding, and scraper status
- you need a real database once you have multiple clubs and historical snapshots
- Django templates are a straightforward replacement for the current inline HTML
- Django admin gives you immediate operational leverage without building internal tools from scratch

Why not keep cloning Flask apps:

- every new club creates another copy to maintain
- fixes to parsing, UI, or hosting have to be repeated
- secrets and deployment settings are mixed into code
- there is no clean tenant model or shared admin surface

Why not choose something simpler than Django:

- FastAPI or plain Flask would work technically, but you would have to build the admin/configuration layer yourself
- a static-site approach is not enough because the system depends on authenticated scraping, persisted snapshots, and per-club configuration

## Target Architecture

### Core model

One Django project: `backnine`

Suggested apps:

- `clubs` for club configuration and branding
- `monitoring` for snapshots, scraper runs, and status
- `dashboard` for public views and JSON endpoints

Suggested tables:

- `Club`
  - `name`
  - `slug`
  - `brs_login_url`
  - `tee_sheet_url`
  - `username`
  - `password`
  - `theme`
  - `hole_pars`
  - `is_active`
- `Snapshot`
  - `club`
  - `scraped_at`
  - `status`
  - `slot_count`
  - `payload`
- `ScrapeRun`
  - `club`
  - `started_at`
  - `finished_at`
  - `status`
  - `error_message`

### Public URLs

- `/` landing page listing clubs
- `/<club-slug>/` public dashboard
- `/<club-slug>/api/data/` JSON data for the dashboard

Examples:

- `/the-heath/`
- `/athenry/`
- `/mountrath/`

If you want the exact branding from your note, that can also be:

- `/the-heath`
- `/round-draft`

Use slugs in the database so a new club is just a new row, not a new app.

### Scraping

Keep Playwright.

The scraper should become shared code, not one file per club. Structure it roughly like this:

- `monitoring/brs/client.py`
- `monitoring/brs/parsers.py`
- `monitoring/services/scrape_club.py`

The scraper input becomes a `Club` record instead of a `config.py` file.

Some clubs may still need custom parser tweaks. Handle that with small per-club strategy flags, not forked codebases.

Examples:

- `parser_variant = "default"`
- `parser_variant = "mountrath"`
- `trim_rules_blocks = true`

### Scheduling

Do not rely on `launchd` or ad hoc shell scripts once this is hosted centrally.

Use one of these:

1. Django + Celery + Redis
2. Django + `django-q2`
3. Django + cron / systemd timer calling a management command

For a first hosted version, cron or systemd timer is enough:

- `python manage.py scrape_club the-heath`
- `python manage.py scrape_all_clubs`

That is simpler than introducing Celery immediately.

### Frontend

Move the inline HTML in `app.py` into Django templates and static assets:

- `templates/dashboard/club_detail.html`
- `static/dashboard/club.css`
- `static/dashboard/club.js`

Keep one shared template and drive the club-specific branding from the `Club` model:

- colors
- title
- hole pars
- maybe logo

That preserves the current UI while removing duplication.

## What To Change First

### Phase 1: normalize the current code

Before adding Django, extract the current common logic into one shared Python package inside this repo:

- one shared scraper module
- one shared parser module
- one shared dashboard template
- per-club config as data, not copied code

This reduces migration risk because you will first prove that all three clubs can run from one codebase.

### Phase 2: add Django around it

Build a Django project that:

- stores club records in the database
- renders dashboards by slug
- serves JSON for the existing frontend
- runs scraper commands against clubs from DB config

### Phase 3: hosted production

Deploy one service with:

- Postgres
- Django app
- Playwright browser dependencies
- periodic scraper jobs

At that point `backnine.ie/<club-slug>/` becomes a normal app route instead of a tunnel URL.

## Risks To Address

### Secrets

The current repo stores live BRS credentials in `config.py`. That should stop before any real deployment.

Move secrets to one of:

- environment variables
- encrypted secret storage
- Django admin fields encrypted at rest if needed

At minimum, never commit live credentials into the shared app.

### Scraper fragility

The real complexity here is not Flask versus Django. It is BRS parsing stability.

Your architecture should assume:

- the DOM may vary by club
- the fallback text parse may need club-specific cleanup
- scraper failures need visible status in admin

### Data growth

Right now each app keeps a rolling JSON file. In Django, decide early whether you want:

- only latest N hours
- daily historical retention
- audit history for troubleshooting

For the current use case, storing snapshots for a rolling window is enough.

## Recommended First Build

If the goal is to move fast without overbuilding, build this first:

1. Django project with `Club` and `Snapshot`
2. one public route `/<club-slug>/`
3. one shared scraper command that reads from `Club`
4. one shared template using the current dashboard UI
5. one admin page to add or disable clubs

That gets you to a real multi-club platform without needing user accounts, billing, or full multi-tenant complexity.

## Bottom Line

Django is a sensible choice here.

Not because the pages are HTML, but because you need:

- one database-backed app for many clubs
- an admin interface
- URL routing by club
- persistent operational state

The simpler alternative is not “stay with separate Flask folders”. The simpler alternative is:

- shared scraper code
- Django app for rendering and admin
- cron-driven scrape jobs at first

That is the approach I would take.
