"""Normalisasi URL, tanggal, dan teks (ACQ05)."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Parameter pelacakan yang dihapus dari URL kanonik.
TRACKING_PARAMS_PREFIXES = ("utm_",)
TRACKING_PARAMS_EXACT = {"fbclid", "gclid", "igshid", "ref", "ref_src", "mc_cid", "mc_eid"}

_WS = re.compile(r"\s+")


def normalize_url(url: str) -> str:
    """Kembalikan URL kanonik: host huruf kecil, tanpa fragment, tanpa parameter pelacakan."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    host = parts.hostname.lower() if parts.hostname else ""
    if host.startswith("www."):
        host = host[4:]
    port = f":{parts.port}" if parts.port and parts.port not in (80, 443) else ""

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=False)
        if not k.lower().startswith(TRACKING_PARAMS_PREFIXES)
        and k.lower() not in TRACKING_PARAMS_EXACT
    ]
    query = urlencode(sorted(query_pairs))
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((scheme, f"{host}{port}", path, query, ""))


def normalize_text(text: str | None) -> str:
    """Rapikan spasi. Mengembalikan string kosong untuk None."""
    if not text:
        return ""
    return _WS.sub(" ", text).strip()


def content_hash(title: str, body: str) -> str:
    """Hash konten untuk kemiripan dan deteksi perubahan. Dipakai bersama kanonikalisasi."""
    normalized = f"{normalize_text(title).lower()}\n{normalize_text(body).lower()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
