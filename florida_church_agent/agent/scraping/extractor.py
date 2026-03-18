"""High-level extraction orchestration for church pages."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from agent.models import RawChurchRecord
from agent.scraping.parsers import extract_contact_fields, extract_social_links


def _guess_name(html: str, fallback: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.text.strip():
        return soup.title.text.strip()[:150]
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    return fallback


def _guess_denomination(text: str) -> str:
    lowered = text.lower()
    for denom in ["Baptist", "Catholic", "Methodist", "Pentecostal", "Lutheran", "Presbyterian"]:
        if denom.lower() in lowered:
            return denom
    return "Unknown"


def extract_record(url: str, html: str, county: str, query: str, provider: str) -> RawChurchRecord:
    contact = extract_contact_fields(html)
    social = extract_social_links(url, html)
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    pastor_match = re.search(r"(?:Pastor|Rev\.?|Reverend)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text)
    service_match = re.search(r"(Sunday[^.]{0,120})", text, flags=re.IGNORECASE)
    host = urlparse(url).netloc.replace("www.", "")
    return RawChurchRecord(
        church_name=_guess_name(html, host),
        denomination=_guess_denomination(text),
        website=url,
        phone=contact["phone"],
        email=contact["email"],
        county=county,
        pastor_name=pastor_match.group(1) if pastor_match else "",
        service_times=service_match.group(1) if service_match else "",
        source_url=url,
        source_query=query,
        source_provider=provider,
        extraction_confidence=0.65,
        **social,
    )
