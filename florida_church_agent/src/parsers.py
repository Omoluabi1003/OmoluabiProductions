"""HTML parsing helpers."""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup


def parse_html(html: str) -> BeautifulSoup:
    """Create BeautifulSoup parser with lxml backend."""
    return BeautifulSoup(html or "", "lxml")


def extract_json_ld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Extract JSON-LD blobs where present."""
    items: list[dict[str, Any]] = []
    for node in soup.select("script[type='application/ld+json']"):
        raw = node.string or node.text
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                items.extend([p for p in parsed if isinstance(p, dict)])
            elif isinstance(parsed, dict):
                items.append(parsed)
        except json.JSONDecodeError:
            continue
    return items


def relevant_subpage_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Find likely helpful subpages for contact/service extraction."""
    keywords = ["contact", "about", "staff", "leadership", "visit", "service", "worship"]
    links: list[str] = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        text = (a.get_text(" ", strip=True) or "").lower()
        if any(k in href.lower() or k in text for k in keywords):
            if href.startswith("http"):
                links.append(href)
            elif href.startswith("/"):
                links.append(base_url.rstrip("/") + href)
    return list(dict.fromkeys(links))[:8]
