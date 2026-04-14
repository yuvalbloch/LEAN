"""
config.py — edit this file before running.
All credentials and tunable parameters live here.

Secrets (API keys, passwords) are read from environment variables.
For convenience, you can put them in a .env file in this directory —
config.py will load it automatically. The .env file is never committed to git.
"""

import os


def _load_dotenv():
    """
    Load a .env file from the same directory as this file, if one exists.
    Lines must be in KEY=VALUE format. Comments (#) and blank lines are ignored.
    Real environment variables always take precedence over the .env file.
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:   # never override a real env var
                os.environ[key] = value

_load_dotenv()


# ── Anthropic ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Email ──────────────────────────────────────────────────────────────────────
EMAIL_TO       = "yuval.bloch2@gmail.com"
EMAIL_FROM     = "my news <yuval.bloch2@gmail.com>"
EMAIL_SUBJECT  = "Your morning digest"

SMTP_HOST     = "smtp.gmail.com"        # or smtp.fastmail.com, etc.
SMTP_PORT     = 587                     # TLS
SMTP_USER     = os.getenv("SMTP_USER",     "yuval.bloch2@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# ── RSS feeds ──────────────────────────────────────────────────────────────────
RSS_FEEDS = [
    # Israel
    "https://www.timesofisrael.com/feed/",
    "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",

    # Global
    "https://www.theguardian.com/world/rss",
    "https://www.france24.com/en/rss",
    "https://rss.dw.com/xml/rss-en-top",

    # Economy
    "https://feeds.bloomberg.com/markets/news.rss",

    # Science
    "https://www.sciencedaily.com/rss/top/science.xml",

    # Positive news
    "https://www.positive.news/feed/",
]
 



# ── Validation ─────────────────────────────────────────────────────────────────

def validate_config():
    """Call once at startup. Raises RuntimeError for each missing required var."""
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY (set the environment variable)")
    if not SMTP_USER:
        missing.append("SMTP_USER (set the environment variable)")
    if not SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD (set the environment variable)")
    if missing:
        raise RuntimeError(
            "Missing required configuration:\n" +
            "\n".join(f"  - {m}" for m in missing)
        )


# ── Digest quotas ──────────────────────────────────────────────────────────────
# These are passed to the AI prompt — they describe the output structure.
QUOTAS = {
    "israel_max": 5,
    "israel_politics_max": 3,
    "global_max": 3,
    "science_economy_max": 2,
    "ai_max": 1,                 # within science/economy
    "positive_min": 2,
    "positive_max": 3,
}
