"""Normalization helpers for source URLs used by research evidence."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_QUERY_KEYS = frozenset({"fbclid", "gclid", "msclkid"})


def normalize_source_url(value: Any) -> str | None:
    """Return a canonical public HTTP(S) URL, or ``None`` for invalid input."""
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError:
        return None

    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").rstrip(".").lower()
    if scheme not in {"http", "https"} or not hostname or parsed.username or parsed.password:
        return None

    default_port = 443 if scheme == "https" else 80
    host_for_url = f"[{hostname}]" if ":" in hostname else hostname
    netloc = host_for_url if port in {None, default_port} else f"{host_for_url}:{port}"

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"

    query = urlencode(
        [
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_QUERY_KEYS
        ],
        doseq=True,
    )
    return urlunsplit((scheme, netloc, path, query, ""))
