"""
critic.py — second-pass hallucination reviewer.

After the summariser generates the digest, the critic reads both the original
source articles and the generated HTML. It inserts an inline annotation
(<span class="critic-note">) after any sentence that is not supported by,
or contradicts, the source material.

The critic never rewrites content and never adds new information — it only
flags. On any failure it returns the original digest unchanged, so a critic
error never blocks email delivery.
"""

import anthropic
import config
from summariser import _format_articles_for_prompt


def review(articles: list[dict], digest_html: str, api_key: str) -> str:
    """
    Run the critic pass on a generated digest.

    Parameters
    ----------
    articles   : filtered source articles (same list passed to summarise())
    digest_html: the full HTML returned by summarise()
    api_key    : Anthropic API key

    Returns
    -------
    The digest HTML, possibly with <span class="critic-note"> annotations
    inserted after flagged sentences. Returns the original digest_html
    unchanged on any error.
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)
        articles_text = _format_articles_for_prompt(articles)

        user_prompt = (
            "Below are the source articles followed by the digest to review.\n\n"
            "━━━ SOURCE ARTICLES ━━━\n\n"
            f"{articles_text}\n\n"
            "━━━ DIGEST TO REVIEW ━━━\n\n"
            f"{digest_html}"
        )

        message = client.messages.create(
            model=config.CRITIC_MODEL,
            max_tokens=8192,
            system=config.CRITIC_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        result = message.content[0].text.strip()

        # Sanity check: the result must still look like HTML.
        # If the model returned plain text or an error message, discard it.
        if "<" not in result or ">" not in result:
            print("Warning: critic returned non-HTML output — using original digest.")
            return digest_html

        return result

    except Exception as e:
        print(f"Warning: critic review failed ({e}) — using original digest.")
        return digest_html
