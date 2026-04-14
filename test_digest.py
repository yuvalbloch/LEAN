"""
test_digest.py — full pipeline run for testing.

Differences from digest.py:
  - Uses claude-haiku for both filter AND summariser (cheaper, faster).
  - Prepends "[TEST]" to the email subject.
"""

import sys
import summariser                          # imported before use so we can patch MODEL
summariser.MODEL = "claude-haiku-4-5-20251001"

from fetcher import fetch_articles
from filter import filter_articles
from summariser import summarise
from emailer import send_email
import config


def main():
    print("Fetching articles...")
    articles = fetch_articles(config.RSS_FEEDS)
    print(f"  {len(articles)} raw articles fetched")

    print("Filtering (AI / haiku)...")
    filtered = filter_articles(articles, config.ANTHROPIC_API_KEY)
    print(f"  {len(filtered)} articles after AI filter")

    if not filtered:
        print("Nothing to summarise.")
        sys.exit(0)

    print("Summarising with Claude Haiku...")
    digest_html = summarise(filtered, config.ANTHROPIC_API_KEY)

    subject = f"[TEST] {config.EMAIL_SUBJECT}"
    print(f"Sending email with subject: {subject!r}...")
    send_email(
        html_body=digest_html,
        subject=subject,
        to_address=config.EMAIL_TO,
        from_address=config.EMAIL_FROM,
        smtp_host=config.SMTP_HOST,
        smtp_port=config.SMTP_PORT,
        smtp_user=config.SMTP_USER,
        smtp_password=config.SMTP_PASSWORD,
    )
    print("Done.")


if __name__ == "__main__":
    main()
