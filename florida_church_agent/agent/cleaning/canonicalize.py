"""Canonicalization helpers."""

from __future__ import annotations

import re
from urllib.parse import urlparse


def canonicalize_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9 ]", "", name.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def canonicalize_website(url: str) -> str:
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    p = urlparse(url)
    host = p.netloc.lower().replace("www.", "")
    return f"https://{host}{p.path.rstrip('/')}"
