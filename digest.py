"""
Personal News Digest
Run once daily (e.g. via cron at 06:45).
"""

import sys
from fetcher import fetch_articles
from filter import filter_articles
from summariser import summarise
from critic import review
from emailer import send_email
import publisher
import config


def main():
    config.validate_config()

    print("Fetching articles...")
    articles = fetch_articles(config.RSS_FEEDS)
    print(f"  {len(articles)} raw articles fetched")

    print("Filtering (AI)...")
    filtered = filter_articles(articles, config.ANTHROPIC_API_KEY)
    print(f"  {len(filtered)} articles after AI filter")

    if not filtered:
        print("Nothing to summarise today.")
        sys.exit(0)

    print("Summarising with Claude...")
    digest_html = summarise(filtered, config.ANTHROPIC_API_KEY)

    print("Running critic review...")
    digest_html = review(filtered, digest_html, config.ANTHROPIC_API_KEY)

    if config.EMAIL_ENABLED:
        print("Sending email...")
        send_email(
            html_body=digest_html,
            subject=config.EMAIL_SUBJECT,
            to_address=config.EMAIL_TO,
            from_address=config.EMAIL_FROM,
            smtp_host=config.SMTP_HOST,
            smtp_port=config.SMTP_PORT,
            smtp_user=config.SMTP_USER,
            smtp_password=config.SMTP_PASSWORD,
        )
    else:
        print("Email skipped (EMAIL_ENABLED = False).")

    if config.BUTTONDOWN_ENABLED:
        print("Publishing to Buttondown...")
        try:
            draft_id = publisher.publish_to_buttondown(
                digest_html, config.EMAIL_SUBJECT, config.BUTTONDOWN_API_KEY
            )
            print(f"  Draft created: {draft_id}")
        except Exception as e:
            print(f"  Buttondown publish failed (email was sent): {e}")

    print("Done.")


if __name__ == "__main__":
    main()