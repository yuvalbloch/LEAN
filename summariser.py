"""
summariser.py — send filtered articles to Claude and get back a formatted HTML digest.
"""

import json
import datetime
import anthropic


MODEL = "claude-opus-4-5"

SYSTEM_PROMPT = """
You are a calm, neutral news editor. Your job is to produce a structured daily digest
from a list of news articles. The reader wants to stay informed without being emotionally
manipulated, doom-scrolled, or overwhelmed.

Strict rules you must always follow:
- No emotional or sensational language. No words like "shocking", "alarming", "crisis",
  "devastating", "explosive", "amid chaos", "fears grow". Use plain factual language.
- No ALL CAPS words. No exclamation marks.
- Never use "BREAKING" or urgency framing.
- Do not editorialize or express opinions. Report what happened.
- If a story is ambiguous or contested, note that briefly; do not pick a side.
- The tone should be like a well-edited printed newspaper — informative, calm, complete.

Output format: valid HTML only, no markdown, no code fences.
Use the exact HTML structure shown in the user prompt.
""".strip()


def summarise(articles: list[dict], api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    articles_text = _format_articles_for_prompt(articles)
    today = datetime.date.today().strftime("%A, %B %d").replace(" 0", " ")

    user_prompt = f"""
Today is {today}.

Below are {len(articles)} news articles fetched from RSS feeds in the last 24 hours.
Produce a daily digest in the following HTML structure. Fill in real content from the
articles — do not invent or hallucinate facts.

━━━ OUTPUT STRUCTURE ━━━

Return only the HTML below (no <html>, <head>, <body> wrappers needed).
Replace every [PLACEHOLDER] with real content derived from the articles.

<div class="digest">

  <div class="section" id="israel">
    <h2>Israel</h2>
    <!-- Up to 5 items. No more than 3 about domestic politics. -->
    <!-- Each item: one factual paragraph, max 3 sentences. Cite source. -->
    [ISRAEL ITEMS]
  </div>

  <div class="section" id="world">
    <h2>World</h2>
    <!-- Up to 3 items. -->
    [WORLD ITEMS]
  </div>

  <div class="section" id="science-economy">
    <h2>Science &amp; Economy</h2>
    <!-- Up to 2 items. At most 1 about AI specifically. -->
    [SCIENCE ECONOMY ITEMS]
  </div>

  <div class="section" id="good-news">
    <h2>Good news</h2>
    <!-- 2–3 items. Must be clearly positive without a common negative interpretation.
         Valid: end of a war, renewable energy milestone, medical breakthrough, species recovery.
         Invalid: "stock market up" (could reverse), political victories (divisive). -->
    [GOOD NEWS ITEMS]
  </div>

  [DEEP_DIVE_BLOCK]

</div>

For each news item, use this HTML pattern:
<div class="item">
  <p class="body">[SUMMARY — 2–3 factual sentences, plain language, no emotional words]</p>
  <p class="source">Source: [SOURCE NAME]</p>
</div>

For [DEEP_DIVE_BLOCK]: if one topic appeared in 3 or more articles across different sources,
write a longer analysis in this structure:

<div class="deep-dive">
  <p class="meta">Today's deep dive · ~15 min read · appeared in [N] sources</p>
  <h2>[TOPIC TITLE]</h2>
  <h3>Abstract</h3>
  <p>[2–3 sentence summary of the event and why it matters]</p>
  <h3>Background</h3>
  <p>[Historical context, 1–2 paragraphs]</p>
  <h3>What happened</h3>
  <p>[Factual account of today's developments, 1–2 paragraphs]</p>
  <h3>Discussion</h3>
  <p><strong>Perspective A:</strong> [One reasonable interpretation or position]</p>
  <p><strong>Perspective B:</strong> [A different reasonable interpretation or position]</p>
</div>

If no topic qualifies for a deep dive, omit [DEEP_DIVE_BLOCK] entirely.

━━━ ARTICLES ━━━

{articles_text}
""".strip()

    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_html = message.content[0].text.strip()
    return _wrap_in_email_template(raw_html, today)


# ── helpers ────────────────────────────────────────────────────────────────────

def _format_articles_for_prompt(articles: list[dict]) -> str:
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(
            f"[{i}] SOURCE: {a['source']}\n"
            f"    TITLE: {a['title']}\n"
            f"    SUMMARY: {a['description']}\n"
            f"    URL: {a['link']}"
        )
    return "\n\n".join(lines)


def _wrap_in_email_template(body_html: str, date_str: str) -> str:
    """Wrap the AI-generated body in a minimal, readable email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your morning digest — {date_str}</title>
<style>
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 16px;
    line-height: 1.7;
    color: #1a1a1a;
    background: #ffffff;
    max-width: 640px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}
  .header {{
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 1rem;
    margin-bottom: 2rem;
  }}
  .header .label {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    letter-spacing: 0.1em;
    color: #888;
    text-transform: uppercase;
  }}
  .header h1 {{
    font-size: 22px;
    font-weight: normal;
    margin: 0.4rem 0 0;
    letter-spacing: -0.02em;
  }}
  .section {{
    margin-bottom: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e0e0e0;
  }}
  .section:first-child {{ border-top: none; padding-top: 0; }}
  h2 {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    font-weight: normal;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #888;
    margin: 0 0 1rem;
  }}
  .item {{
    border-left: 2px solid #d0d0d0;
    padding-left: 1rem;
    margin-bottom: 1.2rem;
  }}
  #good-news .item {{ border-left-color: #6aaa4a; }}
  .body {{ margin: 0; }}
  .source {{
    font-family: Arial, sans-serif;
    font-size: 12px;
    color: #aaa;
    margin: 0.3rem 0 0;
  }}
  .deep-dive {{
    background: #f7f7f5;
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 2rem;
  }}
  .deep-dive .meta {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    color: #aaa;
    letter-spacing: 0.05em;
    margin: 0 0 0.8rem;
  }}
  .deep-dive h2 {{
    font-family: Georgia, serif;
    font-size: 18px;
    font-weight: normal;
    letter-spacing: -0.01em;
    text-transform: none;
    color: #1a1a1a;
    margin: 0 0 1rem;
  }}
  .deep-dive h3 {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    font-weight: normal;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #888;
    margin: 1.2rem 0 0.4rem;
  }}
  .footer {{
    border-top: 1px solid #e0e0e0;
    margin-top: 2rem;
    padding-top: 0.8rem;
    font-family: Arial, sans-serif;
    font-size: 11px;
    color: #bbb;
  }}
  .mantra {{
    margin: 2rem 0;
    padding: 1.5rem 1.75rem;
    border-radius: 6px;
    background: #f7f7f5;
    border-left: 3px solid #c8c8c4;
  }}
  .mantra p {{
    font-family: Georgia, serif;
    font-size: 15px;
    line-height: 1.9;
    color: #555;
    margin: 0 0 0.6rem;
  }}
  .mantra p:last-child {{
    margin: 0;
  }}
  .mantra .greeting {{
    font-size: 17px;
    color: #333;
    margin-bottom: 1rem;
  }}
  .critic-note {{
    font-family: Arial, sans-serif;
    font-size: 11px;
    color: #b05000;
    background: #fff8f0;
    border: 1px solid #f0c080;
    border-radius: 3px;
    padding: 1px 4px;
    margin-left: 4px;
  }}
</style>
</head>
<body>
  <div class="header">
    <p class="label">Your morning digest</p>
    <h1>{date_str}</h1>
  </div>

  <div class="mantra">
    <p class="greeting">Good morning, Yuval.</p>
    <p>You are about to read a summary of the current state of the world.</p>
    <p>Remember:<br>
    The facts of the world do not change based on whether you like them or not.<br>
    Your beliefs matter only through the actions you take.</p>
    <p>Approach this with a beginner's mind — aim for clarity, not certainty.</p>
    <p>You do not need to know every detail.<br>
    Understand enough to see the bigger picture,<br>
    so you can make better decisions and contribute in a meaningful way.</p>
  </div>

  {body_html}

  <div class="mantra" style="border-left-color: #a8c8a0; margin-top: 2.5rem;">
    <p>You have finished reading your summary of the world.</p>
    <p>Now step away, focus on what matters,<br>
    and do your part to make it better.</p>
  </div>

  <div class="footer">
    Generated automatically from RSS feeds · no tracking · no ads
  </div>
</body>
</html>"""