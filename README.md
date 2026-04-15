# LEAN — Personal News Digest

A self-hosted daily news pipeline that fetches RSS articles, filters and ranks them with Claude AI, generates a structured HTML digest, and delivers it by email each morning.

**LEAN** is designed around one principle: stay informed without being emotionally manipulated. No sensationalism, no exclamation marks, no doom-scrolling — just calm, factual summaries from sources you choose.

For design intent and editorial principles, see [PHILOSOPHY.md](PHILOSOPHY.md).

## Pipeline

```
fetch → filter (Haiku) → summarise (Opus) → critic review (Haiku) → email
```

1. **Fetch** — pulls articles from RSS feeds published in the last 24 hours
2. **Filter** — deduplicates by title similarity, then Claude Haiku ranks by relevance
3. **Summarise** — Claude Opus generates a structured HTML digest in four sections
4. **Critic review** — a second Claude Haiku pass reads both the source articles and the
   generated digest, and inserts inline warning annotations next to any claim it cannot
   verify against the sources. If it finds nothing wrong, the digest is returned unchanged.
5. **Email** — sent via SMTP with an HTML/plain-text fallback

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

> **Requires Python 3.10+.** Use `python3` to ensure you get the right version
> (`python` on some systems still points to Python 2 or 3.6).

**2. Create a `.env` file**

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...       # your Anthropic API key
SMTP_USER=you@gmail.com            # your Gmail address (or other SMTP login)
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Gmail app password — not your account password
```

`config.py` loads this file automatically at startup. You never need to export
these variables manually. The `.env` file stays on your machine and is never
committed to git.

**3. Adjust settings in `config.py`**

- `EMAIL_TO` / `EMAIL_FROM` / `EMAIL_SUBJECT` — delivery addresses
- `RSS_FEEDS` — list of feed URLs to pull from
- `DIGEST_SECTIONS` — per-section output limits passed to Claude

See [config_guide.md](config_guide.md) for a full reference of every available setting.

## Run

```bash
python3 digest.py
```

If a required credential is missing, the script will print a clear error
message listing exactly which values need to be set in `.env`.

## Tests

```bash
python3 tests.py
```

44 tests covering all pure functions (no API calls, no network). The one
exception is `test_critic_catches_clear_error`, which calls the real Anthropic
API and is skipped automatically if `ANTHROPIC_API_KEY` is not set.

## Credentials and security

- Secrets live in `.env` only — never in `config.py` or committed to git
- `.env` is listed in `.gitignore`
- If you have shared or synced this repo before, rotate your Gmail app password
  and Anthropic API key, as they were previously hardcoded in `config.py`

## Scheduling

For server deployment (Vultr, DigitalOcean, etc.), see [DEPLOYMENT.md](DEPLOYMENT.md).

### Windows (Task Scheduler)

Because credentials are loaded from the `.env` file, you do not need to set
system-wide environment variables. Create a basic task that runs daily at your
preferred time with:

- **Program:** `python3`
- **Arguments:** `digest.py`
- **Start in:** full path to this folder (e.g. `C:\Users\you\OneDrive\Desktop\LEAN`)

To log output, use a wrapper `.bat` file instead:

```bat
cd /d C:\Users\you\OneDrive\Desktop\LEAN
python3 digest.py >> digest.log 2>&1
```

### Linux / macOS (cron)

Run `crontab -e` and add:

```
45 6 * * * cd /path/to/LEAN && python3 digest.py >> /tmp/digest.log 2>&1
```

Use `python3`, not `python`.

## Responsibility

This digest is an informational tool, not professional advice (financial, legal,
medical, or safety-critical). Always verify important claims with primary sources
before acting. Content is AI-generated and has not been personally reviewed.

## License

MIT — see [LICENSE](LICENSE).
