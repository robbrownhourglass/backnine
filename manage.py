#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from backnine_shared.clubs import build_runtime_config, list_club_slugs
from backnine_shared.scraper import run_scraper


ROOT_DIR = Path(__file__).resolve().parent


def runtime_config(slug: str):
    data_dir = ROOT_DIR / "data" / slug
    data_dir.mkdir(parents=True, exist_ok=True)
    return type("Config", (), build_runtime_config(slug, data_dir))


def serve(args):
    from app import app

    app.run(host="0.0.0.0", port=args.port, debug=False)


def scrape(args):
    asyncio.run(run_scraper(runtime_config(args.slug)))


def scrape_all(args):
    async def runner():
        await asyncio.gather(*(run_scraper(runtime_config(slug)) for slug in list_club_slugs()))

    asyncio.run(runner())


def show_config(args):
    config = runtime_config(args.slug)
    print(config.CLUB_SLUG, config.CLUB_NAME, config.DASHBOARD_PORT, config.DATA_FILE)


def main():
    parser = argparse.ArgumentParser(description="Back Nine unified runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run the unified web app")
    serve_parser.add_argument("--port", type=int, default=5080)
    serve_parser.set_defaults(func=serve)

    scrape_parser = subparsers.add_parser("scrape", help="Run scraper for one club")
    scrape_parser.add_argument("slug", choices=list_club_slugs())
    scrape_parser.set_defaults(func=scrape)

    scrape_all_parser = subparsers.add_parser("scrape-all", help="Run scrapers for all clubs")
    scrape_all_parser.set_defaults(func=scrape_all)

    config_parser = subparsers.add_parser("show-config", help="Print resolved config for one club")
    config_parser.add_argument("slug", choices=list_club_slugs())
    config_parser.set_defaults(func=show_config)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
