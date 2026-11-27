from datetime import datetime, timedelta, timezone

import pytest

from mediawatch.normalize import content_hash, normalize_url
from mediawatch.parse_article import ParseError, parse_article
from mediawatch.pipeline import build_record, dedupe

ARTICLE_HTML = """
<html><head>
  <title>Fallback title</title>
  <meta property="og:title" content="Layanan Merek Contoh pulih  bertahap" />
  <meta property="og:description" content="Ringkasan singkat berita." />
  <meta property="article:published_time" content="2026-11-26T09:30:00+07:00" />
  <meta name="author" content="Redaksi Contoh" />
  <meta property="article:section" content="Ekonomi" />
  <link rel="canonical" href="https://www.contoh-media.example/ekonomi/layanan-pulih/" />
</head><body>
  <p>Paragraf pertama berisi fakta.</p>
  <p>   Paragraf kedua   dengan spasi berlebih.</p>
</body></html>
"""

NO_DATE_HTML = """
<html><head>
  <meta property="og:title" content="Berita tanpa tanggal" />
</head><body><p>Isi.</p></body></html>
"""

LOGIN_HTML = '<html><body><form><input type="password" name="password"></form></body></html>'
CHALLENGE_HTML = "<html><body>Please enable JavaScript and complete the CAPTCHA</body></html>"


def test_normalize_url_strips_tracking_and_www_and_trailing_slash():
    url = "https://WWW.Contoh-Media.example/Ekonomi/Layanan/?utm_source=x&id=42&fbclid=abc#bagian"
    assert normalize_url(url) == "https://contoh-media.example/Ekonomi/Layanan?id=42"


def test_normalize_url_is_idempotent():
    url = "https://contoh-media.example/a/b/?utm_medium=y"
    once = normalize_url(url)
    assert normalize_url(once) == once


def test_content_hash_ignores_whitespace_and_case():
    assert content_hash("Judul  Berita", "Isi") == content_hash("judul berita", " Isi ")


def test_parse_uses_canonical_and_keeps_missing_fields_empty_not_fabricated():
    parsed = parse_article(ARTICLE_HTML, "https://contoh-media.example/x?utm_source=a")
    assert parsed.canonical_url == "https://contoh-media.example/ekonomi/layanan-pulih"
    assert parsed.published_at == datetime(2026, 11, 26, 9, 30, tzinfo=timezone(timedelta(hours=7)))
    assert parsed.missing_fields == []
    assert parsed.body is None  # body tidak disimpan bila sumber tidak mengizinkan


def test_missing_timestamp_is_none_not_fetched_time():
    parsed = parse_article(NO_DATE_HTML, "https://contoh-media.example/a")
    assert parsed.published_at is None
    assert "published_at" in parsed.missing_fields


def test_body_is_collected_only_when_allowed_and_whitespace_normalized():
    parsed = parse_article(ARTICLE_HTML, "https://contoh-media.example/x", body_allowed=True)
    assert parsed.body == "Paragraf pertama berisi fakta.\nParagraf kedua dengan spasi berlebih."


@pytest.mark.parametrize("html", [LOGIN_HTML, CHALLENGE_HTML])
def test_login_and_challenge_pages_are_failures_not_empty_success(html):
    with pytest.raises(ParseError):
        parse_article(html, "https://contoh-media.example/a")


def test_build_record_marks_metadata_only_access_and_parser_version():
    record = build_record(
        html=ARTICLE_HTML,
        url="https://contoh-media.example/x",
        workspace_id="ws-1",
        source_id="src-1",
        body_allowed=False,
        fetched_at=datetime(2026, 11, 27, tzinfo=timezone.utc),
    )
    assert record.access_method == "metadata_only"
    assert record.body is None
    assert record.parser_version == "news-v1"
    assert record.fetched_at != record.published_at


def test_dedupe_repeated_fetch_of_same_canonical_url_adds_no_unique_document():
    first = build_record(html=ARTICLE_HTML, url="https://contoh-media.example/x", workspace_id="ws-1", source_id="s", body_allowed=False)
    again = build_record(html=ARTICLE_HTML, url="https://contoh-media.example/x?utm_source=feed", workspace_id="ws-1", source_id="s", body_allowed=False)
    seen: set[str] = set()
    unique = dedupe([first, again], seen)
    assert len(unique) == 1
    assert dedupe([again], seen) == []
