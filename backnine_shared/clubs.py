from __future__ import annotations

import json
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_CONFIG_PATH = ROOT_DIR / "config" / "clubs.json"
SECRET_CONFIG_PATH = ROOT_DIR / "secrets" / "clubs.local.json"
RENDER_SECRET_CONFIG_PATH = Path("/etc/secrets/clubs.local.json")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _read_secret_config() -> dict:
    inline_json = os.environ.get("SECRET_CONFIG_JSON")
    if inline_json:
        return json.loads(inline_json)
    if RENDER_SECRET_CONFIG_PATH.exists():
        return _read_json(RENDER_SECRET_CONFIG_PATH)
    return _read_json(SECRET_CONFIG_PATH)


def load_club_definition(slug: str) -> dict:
    public_data = _read_json(PUBLIC_CONFIG_PATH).get("clubs", {})
    secret_data = _read_secret_config().get("clubs", {})

    if slug not in public_data:
        raise KeyError(f"Unknown club slug: {slug}")

    merged = dict(public_data[slug])
    merged.update(secret_data.get(slug, {}))
    merged["slug"] = slug
    return merged


def list_club_slugs() -> list[str]:
    public_data = _read_json(PUBLIC_CONFIG_PATH).get("clubs", {})
    return sorted(public_data.keys())


def build_runtime_config(slug: str, base_dir: Path) -> dict:
    base_dir = Path(base_dir)
    club = load_club_definition(slug)
    data_file = club.get("data_file", "tee_data.json")

    return {
        "CLUB_SLUG": slug,
        "CLUB_NAME": club["club_name"],
        "APP_TITLE": club.get("app_title", f"{club['club_name']} Tee Monitor"),
        "BRS_USERNAME": club.get("brs_username", ""),
        "BRS_PASSWORD": club.get("brs_password", ""),
        "BRS_LOGIN_URL": club["brs_login_url"],
        "TEE_SHEET_URL": club["tee_sheet_url"],
        "SCRAPE_INTERVAL": club.get("scrape_interval", 120),
        "HISTORY_HOURS": club.get("history_hours", 5),
        "DASHBOARD_PORT": club["dashboard_port"],
        "DATA_FILE": str(base_dir / data_file),
        "HOLE_PARS": club["hole_pars"],
        "THEME": club.get("theme", {}),
        "PARSER": club.get("parser", {}),
        "MAX_SNAPSHOT_AGE_SECONDS": club.get("max_snapshot_age_seconds", 600),
    }
