# Tee Monitor Course Migration Guide

This document is the runbook for migrating this project from one BRS club/course to another.

Use it when changing source club (login, tee sheet parsing, UI branding, and background service setup).

## 1) Pre-Migration Safety

1. Do not stop or overwrite an existing production instance in another directory.
2. Run each course in its own directory and (if needed) its own launchd label.
3. Use a different local dashboard port per instance to avoid collisions.

## 2) Required Config Changes

Edit [config.py](/Users/robertbrown/tee-monitor-athenry/config.py):

1. `BRS_USERNAME`
2. `BRS_PASSWORD`
3. `BRS_LOGIN_URL` (example: `https://members.brsgolf.com/<club>/login`)
4. `TEE_SHEET_URL` (example: `https://members.brsgolf.com/<club>/tee-sheet/1`)
5. `DASHBOARD_PORT` (set unique port if another instance exists, e.g. `5060`)

## 3) Scraper Login Source of Truth

Confirm [scraper.py](/Users/robertbrown/tee-monitor-athenry/scraper.py) uses config-driven login:

1. `login()` should call `page.goto(config.BRS_LOGIN_URL, ...)` (not hardcoded club URL).

## 4) Scraper Validation Protocol (Do This First)

Before dashboard/tunnel, run scraper only:

```bash
/usr/local/bin/python3 scraper.py
```

Look for:

1. `✓ Login submitted`
2. `✓ Logged in. Starting scrape loop...`
3. successful slot captures (`✓ N slots captured`)

Stop with `Ctrl+C` after 1-2 cycles and inspect data:

```bash
/usr/local/bin/python3 -c "import json;d=json.load(open('tee_data.json'));s=d['snapshots'][-1];print(d['status'],d['last_scrape'],s['url'],s['slot_count'])"
```

## 5) Common Breakpoints by New Course

### A) Selector mismatch (most common)

Symptom:

1. `Tee sheet selector not found — trying text-based parse.`

Action:

1. This is acceptable short-term if fallback outputs clean slots.
2. If fallback is noisy, tighten `parse_tee_sheet_from_text()` and `extract_players_from_slot_lines()`.

What helped here:

1. Trim long non-slot blocks (e.g., local rules/terms) before extraction.
2. Ignore metadata tokens like `BOOKING INFO`, `DETAIL`, `ADDITIONAL LOCAL RULES`.
3. Use stricter player-name detection patterns.

### B) Polluted first slot (rules text mixed with booking)

Symptom:

1. First slot contains huge policy/rules text in `players` or `raw`.

Action:

1. Add stop-token trimming in fallback parser (e.g., at `ADDITIONAL LOCAL RULES`).
2. Skip unknown chunks that have no booking state and no plausible names.

### C) Login succeeds but reverts to `/login`

Symptom:

1. scraper status `login_failed` or loop re-enters login repeatedly.

Action:

1. Re-check credentials and `BRS_LOGIN_URL`.
2. Re-check field selectors in `login()` if BRS form layout changed.

## 6) UI Migration Checklist

Edit [app.py](/Users/robertbrown/tee-monitor-athenry/app.py):

1. Page title and header branding (club name).
2. Theme/background colors to match target club branding.
3. Keep high-contrast group dots if needed (`.hole-group-dot`).

Current high-contrast approach:

1. Dots forced to yellow (`#f3d43b`) for visibility on blue backgrounds.

## 7) Course Geometry (Important)

The course projection uses per-hole "wells".

Rule:

1. `wells = par - 1` per hole.

Set in [app.py](/Users/robertbrown/tee-monitor-athenry/app.py):

1. `HOLE_PARS = [...]` (18 values)
2. `HOLE_WELLS = HOLE_PARS.map(par => par - 1)`

For Athenry, pars are:

1. `4,4,3,4,4,3,4,5,4,5,4,3,4,4,4,4,3,4`

## 8) Full Pipeline Start (After Scraper Validation)

Run:

```bash
bash start.sh
```

Check:

1. scraper starts
2. dashboard starts on configured port
3. cloudflared creates quick tunnel URL in `logs/tunnel.log`

Extract URL:

```bash
rg -o "https://[a-z0-9\\-]+\\.trycloudflare\\.com" logs/tunnel.log | tail -n 1
```

## 9) Background Service (Persistent After SSH Logout)

Do not rely on foreground `python3 app.py` / `python3 scraper.py`.

Use launchd. For this repo:

1. install script: [install_launch_agent_athenry.sh](/Users/robertbrown/tee-monitor-athenry/install_launch_agent_athenry.sh)
2. launchd label: `com.tee-monitor-athenry`

Install/load:

```bash
./install_launch_agent_athenry.sh
```

Check status:

```bash
launchctl print gui/$(id -u)/com.tee-monitor-athenry | rg 'state =|pid =|runs ='
```

Stop/start:

```bash
launchctl bootout gui/$(id -u)/com.tee-monitor-athenry
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.tee-monitor-athenry.plist
```

## 10) Final Acceptance Checklist

1. `tee_data.json` updates every scrape interval.
2. `status` settles at `ok`.
3. latest snapshot URL matches target club tee sheet.
4. slot data is sensible (no huge rules blobs in players/raw rows).
5. dashboard loads with correct branding/theme.
6. tunnel URL responds `HTTP 200`.
7. launchd service remains running after SSH disconnect.

## 11) Notes for Future Agents

1. Always validate scraper-only first; UI and tunnel come second.
2. Assume each club may have different BRS DOM nuances.
3. Prefer minimal, reversible changes and verify with logs after each chunk.
4. Never reuse an existing launchd label if another live instance depends on it.
