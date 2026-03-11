# Shared Runtime

## What changed

The three club folders now act as thin runtime wrappers.

The root of the repo is now also a real unified app runtime.

Shared code lives in:

- `backnine_shared/clubs.py`
- `backnine_shared/dashboard.py`
- `backnine_shared/scraper.py`

Public club metadata lives in:

- `config/clubs.json`

Secrets live in:

- `secrets/clubs.local.json`

## Secret file

Path:

- `/Users/robertbrown/backnine/secrets/clubs.local.json`

Template:

- `config/clubs.example.secrets.json`

Suggested permissions:

```bash
chmod 600 /Users/robertbrown/backnine/secrets/clubs.local.json
```

## How to edit secrets

Open the JSON file directly and edit the `brs_username` / `brs_password` values for each club.

Shape:

```json
{
  "clubs": {
    "the-heath": {
      "brs_username": "your_username",
      "brs_password": "your_password"
    }
  }
}
```

## How runtime config is loaded

Each club folder imports shared settings using its slug and its own folder path. That means:

- club identity is defined in `config/clubs.json`
- credentials are merged in from `secrets/clubs.local.json`
- `tee_data.json` still stays inside each club folder

## Quick validation

Run the unified app from the repo root:

```bash
bash start.sh
```

That starts:

- one web app on port `5080`
- one scraper process per club
- one Cloudflare quick tunnel

Routes:

- `/`
- `/the-heath/`
- `/athenry/`
- `/mountrath/`

You can also run pieces individually:

```bash
python3 manage.py serve --port 5080
python3 manage.py scrape the-heath
python3 manage.py show-config the-heath
```

Or load settings manually:

```bash
python3 -c "from backnine_shared.clubs import load_club_definition; print(load_club_definition('the-heath')['club_name'])"
```
