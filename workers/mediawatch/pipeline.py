"""Pipeline berita: fetch -> parse -> normalisasi -> deduplikasi (ACQ02, ACQ05).

Fungsi ini tidak menulis ke database. Hasilnya berupa record siap simpan.
Penulisan ke Supabase dilakukan oleh lapisan repository yang memakai secret server.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .normalize import content_hash, normalize_url
from .parse_article import ParseError, parse_article


@dataclass
class DocumentRecord:
    workspace_id: str
    source_id: str
    platform: str
    url: str
    canonical_url: str
    title: str
    summary: str | None
    body: str | None
    author: str | None
    category: str | None
    published_at: datetime | None
    fetched_at: datetime
    processed_at: datetime
    content_hash: str
    parser_version: str
    access_method: str
    missing_fields: list[str]


PARSER_VERSION = "news-v1"


def build_record(
    *,
    html: str,
    url: str,
    workspace_id: str,
    source_id: str,
    body_allowed: bool,
    fetched_at: datetime | None = None,
) -> DocumentRecord:
    """Ubah HTML satu artikel menjadi record. Melempar ParseError bila halaman tidak valid."""
    fetched = fetched_at or datetime.now(timezone.utc)
    parsed = parse_article(html, url, body_allowed=body_allowed)
    text_for_hash = parsed.body or parsed.summary or ""
    return DocumentRecord(
        workspace_id=workspace_id,
        source_id=source_id,
        platform="news",
        url=url,
        canonical_url=normalize_url(parsed.canonical_url),
        title=parsed.title,
        summary=parsed.summary,
        body=parsed.body,
        author=parsed.author,
        category=parsed.category,
        published_at=parsed.published_at,  # None bila tidak diketahui (PRD bagian 15)
        fetched_at=fetched,
        processed_at=datetime.now(timezone.utc),
        content_hash=content_hash(parsed.title, text_for_hash),
        parser_version=PARSER_VERSION,
        access_method="http" if body_allowed else "metadata_only",
        missing_fields=parsed.missing_fields,
    )


def dedupe(records: list[DocumentRecord], seen_canonical: set[str]) -> list[DocumentRecord]:
    """Buang record yang canonical_url-nya sudah pernah diproses dalam workspace yang sama.

    Pengambilan ulang satu URL tidak menambah hitungan dokumen unik (ACQ05).
    """
    unique: list[DocumentRecord] = []
    for record in records:
        if record.canonical_url in seen_canonical:
            continue
        seen_canonical.add(record.canonical_url)
        unique.append(record)
    return unique


__all__ = ["DocumentRecord", "build_record", "dedupe", "ParseError", "PARSER_VERSION"]
