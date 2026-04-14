# LEAN — Implementation Plan

## Phase 1A — Dual-AI Hallucination Review

| # | File(s) | What | Size |
|---|---------|------|------|
| **1** | `config.py` | Remove hardcoded `ANTHROPIC_API_KEY` and `SMTP_PASSWORD` — replace with `os.getenv(...)`, raise `RuntimeError` if missing | S |
| **2** | `critic.py` *(new)* | New module: `review(articles, digest_html, api_key) -> str`. Sends original articles + digest HTML to Claude Haiku. Returns digest with `<span class='critic-note'>⚠ Critic note: ...</span>` inserted after any unsupported claim. Falls back to original HTML silently on any failure | M |
| **3** | `summariser.py` | Add CSS rule for `.critic-note` (amber border, small font) inside `_wrap_in_email_template` — additive, invisible when no notes present | S |
| **4** | `digest.py` | Call `critic.review(filtered, digest_html)` between the summariser and emailer steps | S |
| **5** | `tests.py` | 3 mocked unit tests for `critic.py`: returns string, falls back on bad response, passthrough when no notes | M |

---

## Phase 1B — Better Configuration

| # | File(s) | What | Size |
|---|---------|------|------|
| **6** | `config.py` | Migrate system prompts (`SUMMARISER_SYSTEM_PROMPT`, `CRITIC_SYSTEM_PROMPT`), `FILTER_SUBJECTS`, model names, and article-count caps from the individual modules into `config.py` | S |
| **7** | `summariser.py`, `filter.py`, `critic.py` | Update each module to `import config` and read all constants from there instead of defining them locally | M |
| **8** | `config_guide.md` *(new)* | Document every single setting in `config.py`: what it does, valid values, example. Include a "Quick start checklist." Covers RSS feeds, quotas, prompts, model choices, email, and all new feature flags | M |

---

## Phase 1C — Server Deployment

| # | File(s) | What | Size |
|---|---------|------|------|
| **9** | `config.py` | Final env-var hardening: add `validate_config()` that raises a clear error for each missing required var | S |
| **10** | `DEPLOYMENT.md` *(new)* | Vultr/Ubuntu step-by-step: provision, install Python 3.10+, clone, `pip3 install`, set env vars (exact shell syntax), cron setup with `python3`, log path, troubleshooting section | M |

---

## Phase 2A — GitHub Open-Source

| # | File(s) | What | Size |
|---|---------|------|------|
| **11** | `.env.example` *(new)* | All required env vars with placeholder values and one-line comments (`ANTHROPIC_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`) | S |
| **12** | `.gitignore` *(new)* | `__pycache__/`, `*.pyc`, `.env`, `*.log`, `.DS_Store` | S |
| **13** | `README.md` | Rewrite for a public audience: what LEAN is, prerequisites, setup steps referencing `.env.example`, links to `config_guide.md` and `DEPLOYMENT.md`, tests, license | M |
| **14** | `LICENSE` *(new)* | MIT license, year 2025 | S |
| **15** | `summariser.py`, `config.py` | Replace hardcoded `"Good morning, Yuval."` with `config.DIGEST_GREETING` — last personal identifier in pipeline output | S |

---

## Phase 2B — Mailing List (Buttondown)

| # | File(s) | What | Size |
|---|---------|------|------|
| **16** | `publisher.py` *(new)*, `config.py` | `publish_to_buttondown(html, subject, api_key)` using stdlib `urllib`. Posts as **draft** (safe default). Add `BUTTONDOWN_ENABLED = False` and `BUTTONDOWN_API_KEY` to config | M |
| **17** | `digest.py` | Wire Buttondown step after email, gated on `config.BUTTONDOWN_ENABLED`. Wrapped in `try/except` so a failure never blocks delivery | S |
| **18** | `.env.example` | Add `BUTTONDOWN_API_KEY=` entry | S |

---

## Phase 2C — Hugo Static Website

| # | File(s) | What | Size |
|---|---------|------|------|
| **19** | `hugo_publisher.py` *(new)*, `config.py` | `write_hugo_post(html, date_str, content_dir) -> str` — writes a Hugo-compatible file with YAML front matter into `content/digest/YYYY-MM-DD.html`. Add `HUGO_ENABLED`, `HUGO_CONTENT_DIR`, `HUGO_REPO_DIR` to config | M |
| **20** | `hugo_publisher.py` | `push_hugo_post(file_path, repo_dir)` — `git add → git commit → git push` via `subprocess.run` (no `shell=True`). Raises `RuntimeError` on non-zero return code | M |
| **21** | `digest.py` | Wire Hugo publish step after Buttondown, gated on `config.HUGO_ENABLED`, wrapped in `try/except` | S |
| **22** | `DEPLOYMENT.md` | Add Hugo/GitHub Pages section: clone Hugo repo on server, SSH deploy key setup, set config vars, safety warning about `HUGO_CONTENT_DIR` | M |

---

## Phase 2D — Legal & Attribution

| # | File(s) | What | Size |
|---|---------|------|------|
| **23** | `config.py`, `summariser.py` | Add `LEGAL_DISCLAIMER` HTML constant to config (AI notice, no personal review, source credit). Replace the existing minimal footer in `_wrap_in_email_template` with it | M |
| **24** | `config_guide.md` | Document all Phase 2 settings: greeting, Buttondown, Hugo, disclaimer | S |

---

## Final Pass

| # | File(s) | What | Size |
|---|---------|------|------|
| **25** | `tests.py` | New tests: legal disclaimer present in template, greeting is configurable, Hugo filename format, Buttondown request body structure. All 39 originals must still pass | M |
| **26** | All files | Final secrets audit — grep for `sk-ant-`, personal email, SMTP password. Run `python3 tests.py`. Verify zero hits | S |

---

## Critical Ordering Notes

- **Task 1 must happen before any git commit** — the API key is currently in `config.py`
- **Task 6 must happen before Task 7** — modules can't import what isn't in config yet
- **Run `python3 tests.py` after Tasks 7, 15, and 23** — those are the three tasks most likely to break existing tests
