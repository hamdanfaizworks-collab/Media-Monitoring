"""Ekstraksi artikel berita dari HTML (ACQ02).

Aturan dari PRD:
- Timestamp yang hilang tidak diganti tanggal lain (published_at = None).
- Halaman yang berisi login, challenge, atau isi kosong dianggap gagal, bukan sukses (OPS01).
- Isi artikel hanya disimpan bila sumber mengizinkan (body_allowed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .normalize import normalize_text, normalize_url

CHALLENGE_MARKERS = ("captcha", "cf-challenge", "access denied", "please enable javascript")
LOGIN_MARKERS = ("name=\"password\"", "type=\"password\"")


class ParseError(Exception):
    """Halaman tidak dapat diekstrak secara andal."""


@dataclass
class ParsedArticle:
    title: str
    canonical_url: str
    published_at: datetime | None
    author: str | None
    category: str | None
    summary: str | None
    body: str | None
    missing_fields: list[str] = field(default_factory=list)


def _meta(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return normalize_text(tag["content"])
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_article(html: str, fetched_url: str, body_allowed: bool = False) -> ParsedArticle:
    lowered = html.lower()
    if any(marker in lowered for marker in CHALLENGE_MARKERS):
        raise ParseError("challenge_page")
    if any(marker in lowered for marker in LOGIN_MARKERS):
        raise ParseError("login_page")

    soup = BeautifulSoup(html, "lxml")
    missing: list[str] = []

    canonical_tag = soup.find("link", rel="canonical")
    canonical_raw = canonical_tag["href"] if canonical_tag and canonical_tag.get("href") else None
    canonical = normalize_url(urljoin(fetched_url, canonical_raw) if canonical_raw else fetched_url)

    title = _meta(soup, "og:title", "twitter:title") or (
        normalize_text(soup.title.string) if soup.title and soup.title.string else ""
    )
    if not title:
        raise ParseError("title_missing")

    published = _parse_datetime(_meta(soup, "article:published_time", "pubdate", "date"))
    if published is None:
        missing.append("published_at")

    author = _meta(soup, "author", "article:author")
    if author is None:
        missing.append("author")

    category = _meta(soup, "article:section")
    summary = _meta(soup, "description", "og:description")

    body: str | None = None
    if body_allowed:
        paragraphs = [normalize_text(p.get_text()) for p in soup.find_all("p")]
        body = "\n".join(p for p in paragraphs if p) or None
        if body is None:
            raise ParseError("body_empty")

    if not summary:
        missing.append("summary")

    return ParsedArticle(
        title=title,
        canonical_url=canonical,
        published_at=published,
        author=author,
        category=category,
        summary=summary,
        body=body,
        missing_fields=missing,
    )
