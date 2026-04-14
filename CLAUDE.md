# CLAUDE.md — Personal News Digest

## Project Overview
A daily news pipeline that fetches RSS articles, filters and ranks them with Claude AI, generates a structured HTML digest, and delivers it by email each morning.

See [PHILOSOPHY.md](PHILOSOPHY.md) for the design intent behind this project — the editorial rules enforced on output (no sensationalism, no emotional language) reflect the core goal, not stylistic preferences.

## Pipeline Stages
1. **Fetch** (`fetcher.py`) — Pull articles from RSS feeds published in the last 24 hours
2. **Filter** (`filter.py`) — Deduplicate by title similarity, then rank by relevance via Claude Haiku
3. **Summarise** (`summariser.py`) — Generate categorized HTML digest via Claude Opus
4. **Email** (`emailer.py`) — Send via SMTP with HTML/plain-text fallback

Entry point: `digest.py` — runs the full pipeline end to end.

## Running
```bash
pip install -r requirements.txt
python3 digest.py
```

> **Note:** Use `python3`, not `python`. The default `python` on this machine is 3.6, which does not support the `list[str]` and `X | Y` type syntax used in this project. `python3` resolves to 3.10 and works correctly.

## Tests
Run after any change to `fetcher.py`, `filter.py`, or `summariser.py`:
```bash
python tests.py
```
Tests cover all pure functions (no API calls, no network). All 39 tests should pass.

## Configuration (`config.py`)
All settings live in `config.py`:
- `ANTHROPIC_API_KEY` — Claude API key
- `EMAIL_TO / EMAIL_FROM / EMAIL_SUBJECT` — delivery addresses
- `SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD` — SMTP credentials
- `RSS_FEEDS` — list of feed URLs
- `QUOTAS` — per-category output limits passed to Claude

`SMTP_USER` and `SMTP_PASSWORD` can also be set as environment variables (preferred — keeps secrets out of the file).

## Models Used
- **claude-haiku-4-5-20251001** — fast, cheap article filtering (`filter.py`)
- **claude-opus-4-5** — high-quality digest generation (`summariser.py`)

## Output Structure
Four digest sections: Israel · World · Science & Economy · Good News  
Deep-dive analysis added automatically when a topic appears in 3+ sources.  
Editorial rules: no ALL CAPS, no sensationalism, no exclamation marks.

## Scheduling (cron)
```
45 6 * * * cd /path/to/new_feed_2 && python digest.py >> /tmp/digest.log 2>&1
```

## Dependencies
- `feedparser >= 6.0`
- `anthropic >= 0.25`
