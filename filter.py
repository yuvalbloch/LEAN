"""
filter.py — two-stage AI filter.

Stage 1: deduplicate by title similarity (cheap, no API call).
Stage 2: send titles + descriptions to Claude in one batch call.
         Claude scores each article and returns only the ones worth keeping.
"""

import json
import random
import re
import anthropic


# ── Subject list ───────────────────────────────────────────────────────────────
# Edit this to match your interests. These replace the old keyword list.
SUBJECTS = [
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

MODEL = "claude-haiku-4-5-20251001"   # fast + cheap for filtering
MAX_ARTICLES_TO_AI = 80               # hard cap before the AI call
MAX_ARTICLES_RETURNED = 25            # how many the AI should keep


def filter_articles(articles: list[dict], api_key: str) -> list[dict]:
    shuffled = list(articles)
    random.shuffle(shuffled)

    # Stage 1: cheap dedup (no API call)
    deduped = _deduplicate(shuffled)
    deduped = deduped[:MAX_ARTICLES_TO_AI]

    if not deduped:
        return []

    # Stage 2: AI relevance + importance filter
    kept_indices = _ai_filter(deduped, api_key)
    return [deduped[i] for i in kept_indices]


# ── Stage 1: deduplication ─────────────────────────────────────────────────────

def _normalise(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9 ]", "", title)
    return re.sub(r"\s+", " ", title).strip()


def _deduplicate(articles: list[dict]) -> list[dict]:
    seen_ngrams: dict[tuple, int] = {}   # ngram → index in unique[]
    unique: list[dict] = []
    for article in articles:
        words = _normalise(article["title"]).split()
        ngrams = {tuple(words[i:i+4]) for i in range(len(words) - 3)}
        matched_idx = next(
            (seen_ngrams[ng] for ng in ngrams if ng in seen_ngrams),
            None,
        )
        if matched_idx is not None:
            unique[matched_idx]["source_count"] += 1
        else:
            article["source_count"] = 1
            for ng in ngrams:
                seen_ngrams[ng] = len(unique)
            unique.append(article)
    return unique


# ── Stage 2: AI filter ─────────────────────────────────────────────────────────

def _ai_filter(articles: list[dict], api_key: str) -> list[int]:
    """
    Returns a list of indices (into `articles`) that the AI considers
    relevant and important enough to include in the digest.
    """
    client = anthropic.Anthropic(api_key=api_key)

    subjects_text = "\n".join(f"- {s}" for s in SUBJECTS)
    articles_text = "\n\n".join(
        f"[{i}] [sources: {a.get('source_count', 1)}] {a['title']}\n{a['description'][:300]}"
        for i, a in enumerate(articles)
    )

    prompt = f"""You are filtering news articles for a personal daily digest.

The reader cares about these subjects:
{subjects_text}

For each article below, decide whether to KEEP or SKIP it based on two criteria:
1. It is relevant to at least one subject above.
2. It seems genuinely significant — not routine, not a minor update, not clickbait.
   A high [sources: N] count means the story was reported by N independent feeds —
   treat that as a strong signal of importance.

Return ONLY a JSON array of the indices to keep. Example: [0, 3, 7, 12]
Keep at most {MAX_ARTICLES_RETURNED} articles.
Return nothing else — no explanation, no markdown, just the JSON array.

Articles:
{articles_text}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        indices = json.loads(raw)
        # Validate: must be a list of ints within range
        return [i for i in indices if isinstance(i, int) and 0 <= i < len(articles)]
    except Exception:
        # If parsing fails, fall back to returning all articles
        print(f"  Warning: AI filter response could not be parsed: {raw[:200]}")
        return list(range(len(articles)))