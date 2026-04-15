# config_guide.md — Configuration Reference

Every tunable setting in `config.py` is documented here. Edit `config.py` directly;
this file is a reference, not a config file.

---

## Quick-start checklist

Before running the pipeline for the first time:

1. Set the `ANTHROPIC_API_KEY` environment variable (or add it to `.env`).
2. Set `SMTP_USER` and `SMTP_PASSWORD` (or add them to `.env`).
3. Set `EMAIL_TO` and `EMAIL_FROM` to your delivery address.
4. Review `RSS_FEEDS` — add or remove feeds to match your interests.
5. Review `FILTER_SUBJECTS` — these tell the AI what topics you care about.
6. Run `python3 tests.py` — all tests should pass before the first live run.

---

## Credentials

### `ANTHROPIC_API_KEY`

| | |
|---|---|
| Type | `str` |
| Source | Environment variable `ANTHROPIC_API_KEY` |
| Required | Yes |

Your Anthropic API key. Never hard-code this in `config.py`. Set it as an
environment variable or put it in a `.env` file in the project root.

```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Email delivery

### `EMAIL_TO`

| | |
|---|---|
| Type | `str` |
| Default | `"yuval.bloch2@gmail.com"` |
| Required | Yes |

The recipient address for the digest email.

### `EMAIL_FROM`

| | |
|---|---|
| Type | `str` |
| Default | `"my news <yuval.bloch2@gmail.com>"` |
| Required | Yes |

The sender address as it appears in the From header. You can use the
`Display Name <address>` format.

### `EMAIL_SUBJECT`

| | |
|---|---|
| Type | `str` |
| Default | `"Your morning digest"` |
| Required | Yes |

Subject line for every digest email.

### `SMTP_HOST`

| | |
|---|---|
| Type | `str` |
| Default | `"smtp.gmail.com"` |
| Required | Yes |

Hostname of your outgoing mail server. Common values:
- Gmail: `smtp.gmail.com`
- Fastmail: `smtp.fastmail.com`
- SendGrid: `smtp.sendgrid.net`

### `SMTP_PORT`

| | |
|---|---|
| Type | `int` |
| Default | `587` |
| Required | Yes |

Port for the SMTP connection. Use `587` for STARTTLS (recommended) or
`465` for implicit TLS. Port `25` is unauthenticated and usually blocked.

### `SMTP_USER`

| | |
|---|---|
| Type | `str` |
| Source | Environment variable `SMTP_USER`, fallback to value in config |
| Required | Yes |

SMTP login username (usually your full email address).

### `SMTP_PASSWORD`

| | |
|---|---|
| Type | `str` |
| Source | Environment variable `SMTP_PASSWORD` |
| Required | Yes |

SMTP password or app-specific password. Set via environment variable only —
never store plaintext passwords in `config.py`.

---

## RSS feeds

### `RSS_FEEDS`

| | |
|---|---|
| Type | `list[str]` |
| Required | Yes |

List of RSS feed URLs fetched each run. The fetcher pulls articles published
in the last 24 hours from each feed.

**Guidelines:**
- More feeds = broader coverage, but longer fetch time.
- Redundant feeds (covering the same story from multiple sources) are fine —
  the deduplicator in `filter.py` collapses near-duplicate titles.
- Feeds that rarely publish relevant content waste filter quota; remove them.

---

## Digest sections

### `DIGEST_SECTIONS`

| | |
|---|---|
| Type | `list[dict]` |
| Required | Yes |

Defines the sections of the digest and the constraints passed to Claude.
The summariser builds the prompt template dynamically from this list, so
adding, removing, or reordering entries here immediately changes what
Claude produces — no edits to `summariser.py` needed.

Each entry is a dict with these keys:

| Key | Type | Required | Meaning |
|---|---|---|---|
| `id` | `str` | Yes | HTML `id` attribute; used to generate the section's placeholder name |
| `title` | `str` | Yes | Heading shown in the digest email |
| `max` | `int` | Yes | Maximum number of items Claude should include |
| `min` | `int` | No | Minimum number of items (useful for "good news" guarantees) |
| `sub_constraints` | `list[dict]` | No | Per-topic caps within the section (see below) |
| `notes` | `str` | No | Extra editorial instruction appended to the section comment |

#### `sub_constraints`

A list of `{"topic": "<description>", "max": <int>}` dicts. Each one tells
Claude: within this section, include at most `max` items about `topic`.

**Example — add India with a domestic-politics cap:**
```python
{
    "id": "india",
    "title": "India",
    "max": 3,
    "sub_constraints": [
        {"topic": "domestic politics", "max": 2},
    ],
},
```

**Example — add a section with no sub-constraints:**
```python
{
    "id": "world",
    "title": "World",
    "max": 3,
},
```

**Example — section with a minimum and editorial notes:**
```python
{
    "id": "good-news",
    "title": "Good news",
    "min": 2,
    "max": 3,
    "notes": "Must be clearly positive without a common negative interpretation.",
},
```

These are soft instructions to the AI — it generally follows them but is not
mechanically constrained.

---

## Mantras

Short texts displayed before and after the digest body in the email.

### `DIGEST_GREETING`

| | |
|---|---|
| Type | `str` |
| Default | `"Good morning, Yuval."` |

Rendered as a larger greeting paragraph at the top of the opening mantra block.
Change this to adjust the name or tone of the greeting.

### `MANTRA_OPENING`

| | |
|---|---|
| Type | `list[str]` |

Paragraphs shown before the news digest. Each string in the list becomes one
`<p>` element. Within a string, use `\n` where you want a line break (`<br>`).

Add, remove, or reorder items freely. An empty list removes the opening mantra
(the greeting is still rendered separately via `DIGEST_GREETING`).

### `MANTRA_CLOSING`

| | |
|---|---|
| Type | `list[str]` |

Paragraphs shown after the news digest, in the green-tinted closing block.
Same rules as `MANTRA_OPENING`: one string per paragraph, `\n` for line breaks.

---

## Models

### `FILTER_MODEL`

| | |
|---|---|
| Type | `str` |
| Default | `"claude-haiku-4-5-20251001"` |

Claude model used by `filter.py` for relevance scoring. Haiku is fast and
cheap — this call processes up to 80 article titles per run, so cost matters.

### `SUMMARISER_MODEL`

| | |
|---|---|
| Type | `str` |
| Default | `"claude-opus-4-5"` |

Claude model used by `summariser.py` to generate the digest HTML. Opus
produces the highest-quality, most carefully worded output. Switching to
Haiku or Sonnet will reduce cost but may lower writing quality.

### `CRITIC_MODEL`

| | |
|---|---|
| Type | `str` |
| Default | `"claude-haiku-4-5-20251001"` |

Claude model used by `critic.py` for hallucination review. This pass reads
the full digest HTML plus all source articles, so it handles a large context,
but its job is comparison not creative writing — Haiku is sufficient.

---

## Filter settings

### `FILTER_MAX_ARTICLES_TO_AI`

| | |
|---|---|
| Type | `int` |
| Default | `80` |

Hard cap on the number of articles sent to the AI filter. After deduplication,
the list is truncated to this size before the API call. Prevents runaway
token usage on days with many feeds or unusual feed activity.

### `FILTER_MAX_ARTICLES_RETURNED`

| | |
|---|---|
| Type | `int` |
| Default | `25` |

Instruction passed to the AI: keep at most this many articles. The
summariser receives this filtered list and selects from it per `DIGEST_SECTIONS`.
Increasing this gives the summariser more to choose from but raises cost.

### `FILTER_SUBJECTS`

| | |
|---|---|
| Type | `list[str]` |

Topic descriptions that define what is relevant to you. The AI filter uses
this list to decide whether to keep or skip each article.

**How to write good subjects:**
- Be specific enough to exclude noise, but broad enough not to miss things.
- Each line is one subject area; the AI reads the full list as a set.
- You can add sub-clauses: `"Israel — domestic politics, economy, society"`.

**Current defaults:**
```
Israel — domestic politics, economy, society, infrastructure
Israel — security and military developments
Middle East — regional diplomacy and conflicts
Global geopolitics — major international relations and treaties
Global economy — markets, trade, inflation, central banks
Science — research breakthroughs, environment
Technology — significant developments (not routine product launches)
Climate and energy — policy, renewables, disasters
Positive news — clear human or environmental progress, species recovery, end of conflicts
```

---

## System prompts

### `SUMMARISER_SYSTEM_PROMPT`

| | |
|---|---|
| Type | `str` |

The system prompt sent to the summariser model. It defines the editorial
voice and hard rules (no emotional language, no ALL CAPS, no exclamation
marks). Edit this to adjust tone, add prohibited words, or change the
editorial style.

**Warning:** changing this prompt may break the HTML output structure if
the model stops following the format instructions. Test with `python3
digest.py` before relying on changes.

### `CRITIC_SYSTEM_PROMPT`

| | |
|---|---|
| Type | `str` |

The system prompt for the hallucination-review pass. Instructs the AI to
insert `<span class="critic-note">` annotations after unsupported claims
without rewriting content.

Editing this prompt is rarely necessary unless you want the critic to flag
different categories of issues (e.g. tone violations in addition to factual
errors).

---

## Validation

### `validate_config()`

Called automatically at the start of `digest.py`. Raises `RuntimeError`
listing every missing required variable so you get one clear error instead
of a cryptic failure mid-run.

Required variables checked:
- `ANTHROPIC_API_KEY`
- `SMTP_USER`
- `SMTP_PASSWORD`
