"""
summariser.py — send filtered articles to Claude and get back a formatted HTML digest.
"""

import datetime
import json
import os
import re
import anthropic
import config


_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deep_dive_history.json")


def summarise(articles: list[dict], api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    articles_text = _format_articles_for_prompt(articles)
    today = datetime.date.today().strftime("%A, %B %d").replace(" 0", " ")
    recent_titles = _load_recent_deep_dives()

    user_prompt = f"""
Today is {today}.

Below are {len(articles)} news articles fetched from RSS feeds in the last 24 hours.
Produce a daily digest in the following HTML structure. Fill in real content from the
articles — do not invent or hallucinate facts.

━━━ OUTPUT STRUCTURE ━━━

Return only the HTML below (no <html>, <head>, <body> wrappers needed).
Replace every [PLACEHOLDER] with real content derived from the articles.

<div class="digest">

{_build_sections_prompt(config.DIGEST_SECTIONS)}

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
{_deep_dive_exclusion_note(recent_titles)}
If no topic qualifies for a deep dive, omit [DEEP_DIVE_BLOCK] entirely.

━━━ ARTICLES ━━━

{articles_text}
""".strip()

    message = client.messages.create(
        model=config.SUMMARISER_MODEL,
        max_tokens=4096,
        system=config.SUMMARISER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_html = message.content[0].text.strip()
    title = _extract_deep_dive_title(raw_html)
    if title:
        _save_deep_dive_title(title)
    return _wrap_in_email_template(raw_html, today)


# ── helpers ────────────────────────────────────────────────────────────────────

def _load_recent_deep_dives() -> list[str]:
    """Return deep dive titles recorded in the past 7 days."""
    if not os.path.exists(_HISTORY_FILE):
        return []
    with open(_HISTORY_FILE) as f:
        entries = json.load(f)
    cutoff = datetime.date.today() - datetime.timedelta(days=7)
    return [
        e["title"]
        for e in entries
        if datetime.date.fromisoformat(e["date"]) >= cutoff
    ]


def _save_deep_dive_title(title: str) -> None:
    """Append today's deep dive title and prune entries older than 7 days."""
    entries = []
    if os.path.exists(_HISTORY_FILE):
        with open(_HISTORY_FILE) as f:
            entries = json.load(f)
    today = datetime.date.today()
    entries.append({"date": today.isoformat(), "title": title})
    cutoff = today - datetime.timedelta(days=7)
    entries = [e for e in entries if datetime.date.fromisoformat(e["date"]) >= cutoff]
    with open(_HISTORY_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def _extract_deep_dive_title(html: str) -> str | None:
    """Extract the <h2> title from the deep-dive block, if present."""
    match = re.search(r'class="deep-dive".*?<h2>(.*?)</h2>', html, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _deep_dive_exclusion_note(recent_titles: list[str]) -> str:
    """Build the exclusion instruction injected into the prompt."""
    if not recent_titles:
        return ""
    listed = "\n".join(f"  - {t}" for t in recent_titles)
    return (
        f"\nThe following topics were already covered in deep dives earlier this week"
        f" — do not select any of them:\n{listed}\n"
        f"If one of those topics still qualifies today, pick the next best topic instead.\n"
    )


def _render_mantra_paragraphs(paragraphs: list[str]) -> str:
    """Convert a list of paragraph strings into <p> tags, with \\n → <br>."""
    lines = []
    for p in paragraphs:
        inner = p.replace("\n", "<br>\n    ")
        lines.append(f"    <p>{inner}</p>")
    return "\n".join(lines)


def _build_sections_prompt(sections: list[dict]) -> str:
    """Generate the HTML section template block from config.DIGEST_SECTIONS."""
    parts = []
    for s in sections:
        if "min" in s:
            count_str = f"{s['min']}\u2013{s['max']} items."
        else:
            count_str = f"Up to {s['max']} items."

        sub_parts = [
            f"At most {sc['max']} about {sc['topic']}."
            for sc in s.get("sub_constraints", [])
        ]
        note_parts = [s["notes"]] if "notes" in s else []
        comment = " ".join([count_str] + sub_parts + note_parts)

        placeholder = "[" + s["id"].upper().replace("-", "_") + "_ITEMS]"
        title_html = s["title"].replace("&", "&amp;")

        parts.append(
            f'  <div class="section" id="{s["id"]}">\n'
            f"    <h2>{title_html}</h2>\n"
            f"    <!-- {comment} -->\n"
            f"    {placeholder}\n"
            f"  </div>"
        )
    return "\n\n".join(parts)


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
    <p class="greeting">{config.DIGEST_GREETING}</p>
{_render_mantra_paragraphs(config.MANTRA_OPENING)}
  </div>

  {body_html}

  <div class="mantra" style="border-left-color: #a8c8a0; margin-top: 2.5rem;">
{_render_mantra_paragraphs(config.MANTRA_CLOSING)}
  </div>

  <div class="footer">
    Generated automatically from RSS feeds · no tracking · no ads
  </div>
</body>
</html>"""