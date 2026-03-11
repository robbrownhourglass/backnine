from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone

from playwright.async_api import TimeoutError as PWTimeout
from playwright.async_api import async_playwright


TIME_BLOCK_RE = re.compile(r"\b(?:[01]\d|2[0-3]):[0-5]\d\b")
NAME_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z'\-\.]*(?:\s+[A-Za-z][A-Za-z'\-\.]*){1,3}$")


def load_data(data_file: str) -> dict:
    if os.path.exists(data_file):
        with open(data_file) as f:
            return json.load(f)
    return {"snapshots": [], "last_scrape": None, "status": "starting"}


def save_data(data_file: str, data: dict):
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2)


def prune_old_snapshots(snapshots: list, history_hours: int) -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=history_hours)
    return [s for s in snapshots if datetime.fromisoformat(s["scraped_at"]) > cutoff]


def parser_value(config, key: str, default):
    return getattr(config, "PARSER", {}).get(key, default)


def trim_non_slot_details(lines: list[str], config) -> list[str]:
    stop_tokens = tuple(parser_value(config, "stop_tokens", [
        "ADDITIONAL LOCAL RULES",
        "BOOKING CONDITIONS",
        "TERMS AND CONDITIONS",
    ]))
    trimmed = []
    for line in lines:
        upper = line.upper()
        if any(token in upper for token in stop_tokens):
            break
        trimmed.append(line)
    return trimmed


def extract_players_from_slot_lines(lines: list[str], config) -> list[str]:
    ignore_exact = {
        "UNAVAILABLE",
        "AVAILABLE",
        "BOOKED",
        "OPEN COMPETITION",
        "MEMBER",
        "FORMAT",
        "INFO ICON",
        "DETAIL",
        "BOOKING INFO",
    }
    ignore_exact.update(token.upper() for token in parser_value(config, "ignore_exact", []))

    ignore_contains = [
        " HOLE",
        "STARTING AT",
        "ENDING AT",
        "ENTRY CLOSED",
        "SUNRISE",
        "SUNSET",
    ]
    ignore_contains.extend(token.upper() for token in parser_value(config, "ignore_contains", []))

    players = []
    for line in lines:
        raw = line.strip()
        if not raw:
            continue

        upper = raw.upper()
        if upper in ignore_exact:
            continue
        if upper.startswith("ADDITIONAL LOCAL RULES"):
            continue
        if any(token in upper for token in ignore_contains):
            continue
        if TIME_BLOCK_RE.fullmatch(raw):
            continue
        if upper.startswith("OPEN ") and "COMPETITION" in upper:
            continue
        if upper.startswith("GUEST WITH "):
            players.append(raw)
            continue
        if NAME_LINE_RE.fullmatch(raw) and not any(ch.isdigit() for ch in raw):
            players.append(raw)

    seen = set()
    deduped = []
    for player in players:
        key = player.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(player)
    return deduped


def parse_tee_sheet_from_text(text: str, config) -> list:
    matches = list(TIME_BLOCK_RE.finditer(text))
    if not matches:
        return [{"raw_fallback": text[:3000]}]

    slots = []
    required_tokens = tuple(parser_value(config, "required_tokens", [
        "UNAVAILABLE",
        "AVAILABLE",
        "BOOKED",
        "OPEN COMPETITION",
        "MEMBER",
        "FORMAT",
    ]))

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        lines = trim_non_slot_details(lines, config)
        if not lines or len(lines) < 2:
            continue

        upper_chunk = chunk.upper()
        if not any(token in upper_chunk for token in required_tokens):
            continue

        available = "UNKNOWN"
        if "UNAVAILABLE" in upper_chunk:
            available = "UNAVAILABLE"
        elif "AVAILABLE" in upper_chunk:
            available = "AVAILABLE"

        players = extract_players_from_slot_lines(lines, config)
        booked_word_count = sum(1 for line in lines if line.upper() == "BOOKED")
        if available == "UNKNOWN" and not players and booked_word_count == 0:
            continue

        if players:
            booking_state = "booked_with_names"
        elif booked_word_count > 0:
            booking_state = "booked_generic"
        elif available == "UNAVAILABLE":
            booking_state = "empty_unavailable"
        else:
            booking_state = "open_or_unknown"

        slots.append({
            "time": match.group(0),
            "available": available,
            "booking_state": booking_state,
            "players": ", ".join(players) if players else "",
            "raw": chunk[:1200],
        })

    return slots if slots else [{"raw_fallback": text[:3000]}]


async def parse_tee_sheet(page, config) -> list:
    try:
        await page.wait_for_selector(
            ".tee-sheet, .ts-row, table.teesheet, .booking-row, [class*='tee']",
            timeout=15000,
        )
    except PWTimeout:
        print("  Tee sheet selector not found, falling back to text parsing.")
        text = await page.inner_text("body")
        return parse_tee_sheet_from_text(text, config)

    row_selectors = [
        ".ts-row",
        ".tee-sheet-row",
        "tr.booking-row",
        "[class*='tee-time']",
        "tbody tr",
    ]

    rows = []
    for selector in row_selectors:
        rows = await page.query_selector_all(selector)
        if rows:
            print(f"  Found {len(rows)} rows with selector: {selector}")
            break

    slots = []
    for row in rows:
        try:
            text = (await row.inner_text()).strip()
            if not text:
                continue

            slot = {
                "raw": text,
                "time": None,
                "players": None,
                "available": None,
            }

            cells = await row.query_selector_all("td, .ts-cell, [class*='cell']")
            if cells:
                slot["time"] = (await cells[0].inner_text()).strip()
                if len(cells) > 1:
                    slot["players"] = (await cells[1].inner_text()).strip()
                if len(cells) > 2:
                    slot["available"] = (await cells[2].inner_text()).strip()

            slots.append(slot)
        except Exception as exc:
            print(f"  Row parse error: {exc}")

    if slots:
        return slots

    text = await page.inner_text("body")
    return parse_tee_sheet_from_text(text, config)


async def expand_tee_times(page):
    toggle = page.get_by_text("SHOW PREVIOUS TEETIMES", exact=False).first
    if await toggle.count() > 0:
        await toggle.click()
        await page.wait_for_timeout(1200)
        print("  Expanded previous tee times")


async def login(page, config):
    print("  Logging in...")
    await page.goto(config.BRS_LOGIN_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1500)

    username_selectors = [
        "input[name='username']",
        "input[name='user_name']",
        "input[id='username']",
        "input[placeholder*='USERNAME' i]",
        "input[aria-label*='USERNAME' i]",
        "input[name='email']",
        "input[type='email']",
        "#email",
        "#username",
    ]
    password_selectors = [
        "input[name='password']",
        "input[id='password']",
        "input[type='password']",
        "input[placeholder*='PASSWORD' i]",
        "input[aria-label*='PASSWORD' i]",
        "#password",
    ]

    username_selector = None
    for selector in username_selectors:
        if await page.locator(selector).count() > 0:
            username_selector = selector
            break

    password_selector = None
    for selector in password_selectors:
        if await page.locator(selector).count() > 0:
            password_selector = selector
            break

    if not username_selector or not password_selector:
        raise RuntimeError("Could not find username/password fields on login page.")

    await page.fill(username_selector, config.BRS_USERNAME)
    await page.fill(password_selector, config.BRS_PASSWORD)

    try:
        await page.click(
            "button[type='submit'], input[type='submit'], .login-btn, "
            "button:has-text('Login'), button:has-text('LOGIN')"
        )
    except Exception:
        await page.press(password_selector, "Enter")

    try:
        await page.wait_for_url(lambda url: "/login" not in url.lower(), timeout=12000)
    except PWTimeout:
        pass

    if "/login" in page.url.lower():
        raise RuntimeError("Still on login page after submit.")

    print("  Login submitted")


async def run_scraper(config):
    data = load_data(config.DATA_FILE)
    data["status"] = "starting"
    save_data(config.DATA_FILE, data)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await login(page, config)
        except Exception as exc:
            data["status"] = f"login_failed: {exc}"
            save_data(config.DATA_FILE, data)
            await browser.close()
            return

        print("Logged in. Starting scrape loop.")

        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Scraping...")
                await page.goto(config.TEE_SHEET_URL, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)
                await expand_tee_times(page)

                if "login" in page.url.lower():
                    print("  Session expired, logging in again.")
                    await login(page, config)
                    await page.goto(config.TEE_SHEET_URL, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    await expand_tee_times(page)

                slots = await parse_tee_sheet(page, config)
                now = datetime.now(timezone.utc).isoformat()
                snapshot = {
                    "scraped_at": now,
                    "url": page.url,
                    "slot_count": len(slots),
                    "slots": slots,
                }

                data = load_data(config.DATA_FILE)
                data["snapshots"].append(snapshot)
                data["snapshots"] = prune_old_snapshots(data["snapshots"], config.HISTORY_HOURS)
                data["last_scrape"] = now
                data["status"] = "ok"
                save_data(config.DATA_FILE, data)

                print(f"  Captured {len(slots)} slots. Snapshots kept: {len(data['snapshots'])}")
            except PWTimeout:
                print("  Page timeout; retrying next cycle.")
                data = load_data(config.DATA_FILE)
                data["status"] = "timeout"
                save_data(config.DATA_FILE, data)
            except Exception as exc:
                print(f"  Error: {exc}")
                data = load_data(config.DATA_FILE)
                data["status"] = f"error: {exc}"
                save_data(config.DATA_FILE, data)

            print(f"  Sleeping {config.SCRAPE_INTERVAL}s.")
            await asyncio.sleep(config.SCRAPE_INTERVAL)
