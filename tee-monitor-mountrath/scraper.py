"""Shared scraper wrapper for Mountrath tee monitor."""

import asyncio

import config
from backnine_shared.scraper import run_scraper


if __name__ == "__main__":
    asyncio.run(run_scraper(config))
