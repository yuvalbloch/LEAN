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


# ── Digest sections ────────────────────────────────────────────────────────────
# Defines the sections of the daily digest and the constraints passed to Claude.
#
# Each entry is a dict with:
#   id    (str)  — HTML id for the section div, used as the placeholder name
#   title (str)  — heading shown in the digest
#   max   (int)  — maximum number of items Claude should include
#   min   (int, optional) — minimum number of items (useful for "good news")
#   sub_constraints (list, optional) — per-topic caps within this section,
#       each a dict: {"topic": "<description>", "max": <int>}
#   notes (str, optional) — extra editorial instruction appended to the comment
#
# To add a section (e.g. India): copy an existing entry, give it a new id/title,
# set the counts, and add sub_constraints if you want topic caps within it.
# To remove a section: delete its entry from the list.
DIGEST_SECTIONS = [
    {
        "id": "israel",
        "title": "Israel",
        "max": 5,
        "sub_constraints": [
            {"topic": "domestic politics", "max": 3},
        ],
    },
    {
        "id": "world",
        "title": "World",
        "max": 3,
    },
    {
        "id": "science-economy",
        "title": "Science & Economy",
        "max": 2,
        "sub_constraints": [
            {"topic": "AI specifically", "max": 1},
        ],
    },
    {
        "id": "good-news",
        "title": "Good news",
        "min": 2,
        "max": 3,
        "notes": (
            "Must be clearly positive without a common negative interpretation. "
            "Valid: end of a war, renewable energy milestone, medical breakthrough, species recovery. "
            'Invalid: "stock market up" (could reverse), political victories (divisive).'
        ),
    },
]

# ── Mantras ────────────────────────────────────────────────────────────────────
# Text shown before and after the digest body.
# DIGEST_GREETING renders as a larger greeting paragraph.
# MANTRA_OPENING / MANTRA_CLOSING are lists of paragraphs.
# Within a paragraph, use \n where you want a <br> line break.
DIGEST_GREETING = "Good morning, Yuval."

MANTRA_OPENING = [
    "You are about to read a summary of the current state of the world.",
    "Remember:\nThe facts of the world do not change based on whether you like them or not.\nYour beliefs matter only through the actions you take.",
    "Approach this with a beginner's mind — aim for clarity, not certainty.",
    "You do not need to know every detail.\nUnderstand enough to see the bigger picture,\nso you can make better decisions and contribute in a meaningful way.",
]

MANTRA_CLOSING = [
    "You have finished reading your summary of the world.",
    "Now step away, focus on what matters,\nand do your part to make it better.",
]

# ── Models ─────────────────────────────────────────────────────────────────────
FILTER_MODEL    = "claude-haiku-4-5-20251001"   # fast + cheap for filtering
SUMMARISER_MODEL = "claude-opus-4-5"             # high-quality digest generation
CRITIC_MODEL    = "claude-haiku-4-5-20251001"   # fast + cheap for hallucination review

# ── Filter settings ────────────────────────────────────────────────────────────
FILTER_MAX_ARTICLES_TO_AI = 80    # hard cap on articles sent to the AI filter
FILTER_MAX_ARTICLES_RETURNED = 25  # how many the AI filter should keep

FILTER_SUBJECTS = [
    "Israel — domestic politics, economy, society, infrastructure",
    "Israel — security and military developments",
    "Middle East — regional diplomacy and conflicts",
    "Global geopolitics — major international relations and treaties",
    "Global economy — markets, trade, inflation, central banks",
    "Science — research breakthroughs,  environment",
    "Technology — significant developments (not routine product launches)",
    "Climate and energy — policy, renewables, disasters",
    "Positive news — clear human or environmental progress, species recovery, end of conflicts",
]

# ── System prompts ─────────────────────────────────────────────────────────────
SUMMARISER_SYSTEM_PROMPT = """
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
