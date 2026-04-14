"""
tests.py — unit tests for pure functions (no API calls, no network).

Run:
    python tests.py
    python -m pytest tests.py   (if pytest is installed)
"""

import datetime
import os
import types
import unittest
from unittest.mock import Mock, patch

from fetcher import _clean, _parse_date
from filter import _normalise, _deduplicate
from summariser import _format_articles_for_prompt, _wrap_in_email_template
from critic import review


# ── helpers ───────────────────────────────────────────────────────────────────

def _entry(**kwargs):
    """Build a minimal feedparser-like entry namespace."""
    return types.SimpleNamespace(**kwargs)


def _article(title, source="Test Source", description="desc", link="http://x.com"):
    return {"title": title, "source": source, "description": description, "link": link}


# ── fetcher._clean ────────────────────────────────────────────────────────────

class TestClean(unittest.TestCase):

    def test_strips_html_tags(self):
        self.assertEqual(_clean("<p>Hello world</p>"), "Hello world")

    def test_nested_tags(self):
        self.assertEqual(_clean("<div><strong>text</strong></div>"), "text")

    def test_collapses_whitespace(self):
        self.assertEqual(_clean("foo  bar\nbaz"), "foo bar baz")

    def test_no_html_passthrough(self):
        self.assertEqual(_clean("plain text"), "plain text")

    def test_empty_string(self):
        self.assertEqual(_clean(""), "")

    def test_truncates_at_600(self):
        self.assertEqual(len(_clean("a" * 700)), 600)

    def test_exactly_600_chars_unchanged(self):
        text = "a" * 600
        self.assertEqual(_clean(text), text)

    def test_tags_with_attributes(self):
        self.assertEqual(_clean('<a href="http://x.com">link</a>'), "link")


# ── fetcher._parse_date ───────────────────────────────────────────────────────

class TestParseDate(unittest.TestCase):

    def test_published_parsed(self):
        e = _entry(published_parsed=(2024, 3, 15, 8, 30, 0, 0, 0, 0))
        self.assertEqual(_parse_date(e), datetime.datetime(2024, 3, 15, 8, 30, 0))

    def test_falls_back_to_updated_parsed(self):
        e = _entry(updated_parsed=(2024, 6, 1, 12, 0, 0, 0, 0, 0))
        self.assertEqual(_parse_date(e), datetime.datetime(2024, 6, 1, 12, 0, 0))

    def test_falls_back_to_created_parsed(self):
        e = _entry(created_parsed=(2023, 1, 1, 0, 0, 0, 0, 0, 0))
        self.assertEqual(_parse_date(e), datetime.datetime(2023, 1, 1, 0, 0, 0))

    def test_published_preferred_over_updated(self):
        e = _entry(
            published_parsed=(2024, 3, 15, 8, 0, 0, 0, 0, 0),
            updated_parsed=(2024, 3, 16, 9, 0, 0, 0, 0, 0),
        )
        self.assertEqual(_parse_date(e).day, 15)

    def test_no_date_fields_returns_none(self):
        self.assertIsNone(_parse_date(_entry()))

    def test_none_field_value_returns_none(self):
        e = _entry(published_parsed=None, updated_parsed=None, created_parsed=None)
        self.assertIsNone(_parse_date(e))


# ── filter._normalise ─────────────────────────────────────────────────────────

class TestNormalise(unittest.TestCase):

    def test_lowercases(self):
        self.assertEqual(_normalise("Hello World"), "hello world")

    def test_strips_punctuation(self):
        self.assertEqual(_normalise("foo, bar: baz!"), "foo bar baz")

    def test_collapses_whitespace(self):
        self.assertEqual(_normalise("a  b   c"), "a b c")

    def test_empty_string(self):
        self.assertEqual(_normalise(""), "")

    def test_keeps_numbers(self):
        self.assertIn("42", _normalise("Story 42"))

    def test_strips_leading_trailing_space(self):
        self.assertEqual(_normalise("  hello  "), "hello")


# ── filter._deduplicate ───────────────────────────────────────────────────────

class TestDeduplicate(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(_deduplicate([]), [])

    def test_single_article_kept(self):
        arts = [_article("Israel signs historic peace deal with Jordan")]
        result = _deduplicate(arts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_count"], 1)

    def test_no_duplicates_all_kept(self):
        arts = [
            _article("Israel signs historic peace deal with Jordan"),
            _article("NASA discovers water on the surface of Mars"),
        ]
        result = _deduplicate(arts)
        self.assertEqual(len(result), 2)
        for a in result:
            self.assertEqual(a["source_count"], 1)

    def test_exact_duplicate_collapsed(self):
        arts = [
            _article("Israel signs historic peace deal with Jordan", source="Reuters"),
            _article("Israel signs historic peace deal with Jordan", source="BBC"),
        ]
        result = _deduplicate(arts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_count"], 2)

    def test_near_duplicate_collapsed(self):
        # Share 4-gram "signs historic peace deal"
        arts = [
            _article("Israel signs historic peace deal with Jordan"),
            _article("Netanyahu signs historic peace deal announced today"),
        ]
        result = _deduplicate(arts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_count"], 2)

    def test_three_sources_increments_correctly(self):
        arts = [
            _article("Israel signs historic peace deal with Jordan", source="A"),
            _article("Israel signs historic peace deal with Jordan", source="B"),
            _article("Israel signs historic peace deal with Jordan", source="C"),
        ]
        result = _deduplicate(arts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_count"], 3)

    def test_short_title_no_ngrams_always_kept(self):
        # Titles shorter than 4 words produce no 4-grams → never deduplicated
        arts = [
            _article("War ends"),
            _article("War ends"),
        ]
        result = _deduplicate(arts)
        self.assertEqual(len(result), 2)

    def test_first_article_is_canonical(self):
        arts = [
            _article("Israel signs historic peace deal with Jordan", source="First"),
            _article("Israel signs historic peace deal with Jordan", source="Second"),
        ]
        result = _deduplicate(arts)
        self.assertEqual(result[0]["source"], "First")

    def test_source_count_field_added_to_all(self):
        arts = [
            _article("Israel signs historic peace deal with Jordan"),
            _article("NASA discovers water on the surface of Mars"),
        ]
        result = _deduplicate(arts)
        for a in result:
            self.assertIn("source_count", a)


# ── summariser._format_articles_for_prompt ────────────────────────────────────

class TestFormatArticlesForPrompt(unittest.TestCase):

    def test_single_article_contains_fields(self):
        arts = [{"title": "Test Title", "source": "Reuters",
                 "description": "Some news.", "link": "http://example.com"}]
        result = _format_articles_for_prompt(arts)
        self.assertIn("Test Title", result)
        self.assertIn("Reuters", result)
        self.assertIn("Some news.", result)
        self.assertIn("http://example.com", result)

    def test_numbering_starts_at_1(self):
        arts = [{"title": "A", "source": "S", "description": "D", "link": "L"}]
        result = _format_articles_for_prompt(arts)
        self.assertIn("[1]", result)

    def test_multiple_articles_numbered_sequentially(self):
        arts = [
            {"title": "A", "source": "S1", "description": "D1", "link": "L1"},
            {"title": "B", "source": "S2", "description": "D2", "link": "L2"},
            {"title": "C", "source": "S3", "description": "D3", "link": "L3"},
        ]
        result = _format_articles_for_prompt(arts)
        self.assertIn("[1]", result)
        self.assertIn("[2]", result)
        self.assertIn("[3]", result)
        self.assertNotIn("[0]", result)

    def test_articles_separated(self):
        arts = [
            {"title": "First", "source": "S1", "description": "D1", "link": "L1"},
            {"title": "Second", "source": "S2", "description": "D2", "link": "L2"},
        ]
        result = _format_articles_for_prompt(arts)
        idx_first = result.index("First")
        idx_second = result.index("Second")
        self.assertGreater(idx_second, idx_first)


# ── summariser._wrap_in_email_template ────────────────────────────────────────

class TestWrapInEmailTemplate(unittest.TestCase):

    def setUp(self):
        self.html = _wrap_in_email_template("<p>body content</p>", "Monday, April 13")

    def test_is_valid_html_document(self):
        self.assertTrue(self.html.strip().startswith("<!DOCTYPE html>"))

    def test_contains_date(self):
        self.assertIn("Monday, April 13", self.html)

    def test_contains_body(self):
        self.assertIn("<p>body content</p>", self.html)

    def test_contains_greeting(self):
        self.assertIn("Good morning, Yuval", self.html)

    def test_contains_footer(self):
        self.assertIn("Generated automatically from RSS feeds", self.html)

    def test_different_dates_distinct_output(self):
        html2 = _wrap_in_email_template("<p>body</p>", "Tuesday, April 14")
        self.assertIn("Tuesday, April 14", html2)
        self.assertNotIn("Monday, April 13", html2)


# ── critic.review ─────────────────────────────────────────────────────────────

class TestCritic(unittest.TestCase):

    def _mock_client(self, response_text: str):
        """Return a mock anthropic client whose messages.create returns response_text."""
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = [Mock(text=response_text)]
        mock_client.messages.create.return_value = mock_message
        return mock_client

    def test_review_returns_string(self):
        """review() always returns a str."""
        with patch("critic.anthropic.Anthropic") as mock_cls:
            mock_cls.return_value = self._mock_client("<div>annotated html</div>")
            result = review([], "<div>test</div>", "fake-key")
            self.assertIsInstance(result, str)

    def test_review_fallback_on_non_html_response(self):
        """review() returns the original digest when the API returns no HTML."""
        original = "<div>original digest</div>"
        with patch("critic.anthropic.Anthropic") as mock_cls:
            mock_cls.return_value = self._mock_client("Something went wrong")
            result = review([], original, "fake-key")
            self.assertEqual(result, original)

    def test_review_passthrough_when_no_notes(self):
        """review() returns the digest unchanged when the critic finds no issues."""
        original = "<div><p>Some factual text.</p></div>"
        with patch("critic.anthropic.Anthropic") as mock_cls:
            mock_cls.return_value = self._mock_client(original)
            result = review([], original, "fake-key")
            self.assertEqual(result, original)

    def test_review_fallback_on_exception(self):
        """review() returns the original digest when the API call raises."""
        original = "<div>original</div>"
        with patch("critic.anthropic.Anthropic") as mock_cls:
            mock_cls.side_effect = Exception("Network error")
            result = review([], original, "fake-key")
            self.assertEqual(result, original)

    @unittest.skipUnless(
        os.getenv("ANTHROPIC_API_KEY"),
        "ANTHROPIC_API_KEY not set — skipping live critic integration test"
    )
    def test_critic_catches_clear_error(self):
        """
        Integration test (requires API key).

        The source article says Paris city-proper population is ~2 million.
        The digest claims 15 million — a direct numerical contradiction.
        The critic must insert a critic-note annotation.
        """
        articles = [{
            "title": "Paris population study released",
            "source": "City Statistics Bureau",
            "description": (
                "The city of Paris has a population of approximately 2 million people "
                "in the city proper, according to the latest census data released today."
            ),
            "link": "http://example.com/paris-population",
        }]
        # The digest states 15 million — clearly contradicts the source's 2 million
        digest_html = (
            '<div class="digest">'
            '<div class="section" id="world"><h2>World</h2>'
            '<div class="item">'
            '<p class="body">A new study confirms that Paris, with its city proper '
            "population of 15 million residents, remains one of Europe's most densely "
            "populated capitals.</p>"
            '<p class="source">Source: City Statistics Bureau</p>'
            "</div></div></div>"
        )
        result = review(articles, digest_html, os.getenv("ANTHROPIC_API_KEY"))
        self.assertIn(
            "critic-note",
            result,
            "Expected a critic-note annotation flagging '15 million' vs the source's '2 million'",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
