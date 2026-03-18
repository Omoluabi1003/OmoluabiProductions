"""Field extraction from homepage and related pages."""

from __future__ import annotations

import re
import uuid
from typing import Optional

from bs4 import BeautifulSoup

from src.models import RawChurchRecord
from src.parsers import extract_json_ld, parse_html
from src.utils import clean_whitespace, extract_domain

PHONE_RE = re.compile(r"(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")
SERVICE_RE = re.compile(r"(service(?:s)?\s*times?|worship\s*times?|sunday\s*[0-9:apm\s,]+)", re.IGNORECASE)

DENOMINATION_KEYWORDS = {
    "Baptist": ["baptist"],
    "Catholic": ["catholic", "diocese"],
    "Pentecostal": ["pentecostal", "assembly of god"],
    "Methodist": ["methodist", "umc"],
    "Presbyterian": ["presbyterian", "pcusa"],
    "Non-Denominational": ["non denominational", "independent"],
    "Lutheran": ["lutheran"],
    "Episcopal": ["episcopal"],
}


def _find_social(soup: BeautifulSoup, key: str) -> Optional[str]:
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if key in href.lower():
            return href
    return None


def _infer_denomination(text: str) -> Optional[str]:
    t = text.lower()
    for denom, keywords in DENOMINATION_KEYWORDS.items():
        if any(k in t for k in keywords):
            return denom
    return None


def _extract_name(soup: BeautifulSoup, jsonld_docs: list[dict]) -> Optional[str]:
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return clean_whitespace(h1.get_text(" ", strip=True))
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return clean_whitespace(title.split("|")[0].split("-")[0])
    for doc in jsonld_docs:
        if isinstance(doc.get("name"), str):
            return clean_whitespace(doc["name"])
    return None


def _extract_address_from_jsonld(jsonld_docs: list[dict]) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    for doc in jsonld_docs:
        addr = doc.get("address")
        if isinstance(addr, dict):
            return (
                clean_whitespace(addr.get("streetAddress")),
                clean_whitespace(addr.get("addressLocality")),
                clean_whitespace(addr.get("addressRegion")),
                clean_whitespace(addr.get("postalCode")),
            )
    return None, None, None, None


def _extract_geo(jsonld_docs: list[dict]) -> tuple[Optional[float], Optional[float]]:
    for doc in jsonld_docs:
        geo = doc.get("geo")
        if isinstance(geo, dict):
            try:
                return float(geo.get("latitude")), float(geo.get("longitude"))
            except (TypeError, ValueError):
                pass
    return None, None


def extract_church_record(html: str, source_url: str, county: str) -> RawChurchRecord:
    """Extract a best-effort record from a page's HTML."""
    soup = parse_html(html)
    jsonld_docs = extract_json_ld(soup)
    text = soup.get_text(" ", strip=True)

    church_name = _extract_name(soup, jsonld_docs)
    phone_match = PHONE_RE.search(text)
    email_match = EMAIL_RE.search(text)
    zip_match = ZIP_RE.search(text)
    service_match = SERVICE_RE.search(text)
    street, city, state, zip_code = _extract_address_from_jsonld(jsonld_docs)
    lat, lon = _extract_geo(jsonld_docs)

    pastor_name = None
    for pattern in [r"Pastor\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", r"Lead Pastor\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"]:
        match = re.search(pattern, text)
        if match:
            pastor_name = clean_whitespace(match.group(1))
            break

    if not zip_code and zip_match:
        zip_code = zip_match.group(0)

    inferred_denom = _infer_denomination(" ".join(filter(None, [church_name, text[:4000]])))
    confidence = 0.3
    if church_name:
        confidence += 0.2
    if phone_match:
        confidence += 0.1
    if street and city:
        confidence += 0.2
    if inferred_denom:
        confidence += 0.1
    if service_match:
        confidence += 0.1

    return RawChurchRecord(
        record_id=str(uuid.uuid4()),
        church_name=church_name,
        denomination=inferred_denom,
        website=source_url,
        phone=phone_match.group(0) if phone_match else None,
        email=email_match.group(0) if email_match else None,
        street_address=street,
        city=city,
        state=state or "FL",
        zip_code=zip_code,
        county=county,
        pastor_name=pastor_name,
        service_times=clean_whitespace(service_match.group(0)) if service_match else None,
        facebook_url=_find_social(soup, "facebook.com"),
        instagram_url=_find_social(soup, "instagram.com"),
        youtube_url=_find_social(soup, "youtube.com"),
        latitude=lat,
        longitude=lon,
        source_url=source_url,
        source_domain=extract_domain(source_url),
        confidence_score=min(confidence, 1.0),
    )
