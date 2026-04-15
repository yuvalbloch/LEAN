"""
publisher.py — optional Buttondown newsletter integration.

Publishes the digest as a draft email on Buttondown.
Drafts are never sent automatically — they require manual review and send
in the Buttondown dashboard.

Usage:
    Set BUTTONDOWN_ENABLED = True and BUTTONDOWN_API_KEY in config.py (or .env).
    The digest.py pipeline calls this automatically when enabled.
"""

import json
import re
import urllib.request
import urllib.error


_BUTTONDOWN_API_URL = "https://api.buttondown.email/v1/emails"


def _extract_body_fragment(full_html: str) -> str:
    """
    Buttondown expects an HTML fragment, not a full document.
    Extract the <style> block and <body> content from the full HTML.
    """
    style_match = re.search(r"<style[^>]*>(.*?)</style>", full_html, re.DOTALL)
    style_block = f"<style>{style_match.group(1)}</style>\n" if style_match else ""

    body_match = re.search(r"<body[^>]*>(.*?)</body>", full_html, re.DOTALL)
    body_content = body_match.group(1) if body_match else full_html

    return style_block + body_content


def publish_to_buttondown(html: str, subject: str, api_key: str) -> str:
    """
    Post the digest HTML to Buttondown as a draft.

    Returns the draft email ID (str) on success.
    Raises RuntimeError if the API returns a non-2xx response.
    """
    fragment = "<!-- buttondown-editor-mode: fancy -->\n" + _extract_body_fragment(html)

    payload = json.dumps({
        "subject": subject,
        "body": fragment,
        "status": "draft",
    }).encode("utf-8")

    request = urllib.request.Request(
        _BUTTONDOWN_API_URL,
        data=payload,
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode("utf-8"))
            return body.get("id", "unknown")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Buttondown API error {e.code}: {error_body}"
        ) from e
