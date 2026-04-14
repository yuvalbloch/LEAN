"""
fetcher.py — pull articles published in the last 24 hours from a list of RSS feeds.
Returns a list of dicts: {title, description, link, source, published_utc}
"""

import time
import datetime
import feedparser


MAX_AGE_HOURS = 24


def fetch_articles(feed_urls: list[str]) -> list[dict]:
    articles = []
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=MAX_AGE_HOURS)

    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.get("title", url)

            for entry in feed.entries:
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue  # too old

                articles.append({
                    "title":         entry.get("title", "").strip(),
                    "description":   _clean(entry.get("summary", "")),
                    "link":          entry.get("link", ""),
                    "source":        source_name,
                    "published_utc": published,
                })

        except Exception as exc:
            print(f"  Warning: could not fetch {url}: {exc}")

    return articles


# ── helpers ────────────────────────────────────────────────────────────────────

def _parse_date(entry) -> datetime.datetime | None:
    """Try several feedparser date fields; return a UTC datetime or None."""
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime.datetime(*t[:6])
            except Exception:
                pass
    return None


def _clean(text: str) -> str:
    """Strip HTML tags and excess whitespace from a description string."""
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:600]   # cap at 600 chars to save tokens
