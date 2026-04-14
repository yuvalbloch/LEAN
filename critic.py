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
from summariser import _format_articles_for_prompt


CRITIC_MODEL = "claude-haiku-4-5-20251001"   # fast + cheap; Opus is overkill here

CRITIC_SYSTEM_PROMPT = """
You are a factual accuracy reviewer for a news digest.

You will receive:
1. A numbered list of source articles (title, summary, URL)
2. An HTML digest generated from those articles

Your job: find sentences in the digest that make a factual claim that is NOT
supported by, or that directly contradicts, the source articles provided.

For each such sentence, insert this annotation immediately after it:
<span class="critic-note">⚠ Critic note: [brief explanation of what the source says instead]</span>

Rules you must follow:
- Do NOT rewrite, rephrase, or remove any existing content.
- Do NOT add new information that is absent from both the digest and the sources.
- Do NOT annotate correct or unverifiable information — flag only clear contradictions
  or unsupported specific claims (wrong numbers, wrong names, invented events).
- If you find no issues, return the digest HTML completely unchanged.
- Preserve every existing HTML tag exactly as-is.
- Return only the HTML — no markdown, no code fences, no commentary.
""".strip()


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
            model=CRITIC_MODEL,
            max_tokens=8192,
            system=CRITIC_SYSTEM_PROMPT,
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
