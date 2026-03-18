"""Normalization and validation routines."""

from __future__ import annotations

import re

from src.models import CleanChurchRecord, RawChurchRecord
from src.utils import canonical_website, clean_whitespace

PHONE_DIGITS_RE = re.compile(r"\D")

DENOM_VOCAB = {
    "baptist": "Baptist",
    "catholic": "Catholic",
    "pentecostal": "Pentecostal",
    "methodist": "Methodist",
    "presbyterian": "Presbyterian",
    "lutheran": "Lutheran",
    "episcopal": "Episcopal",
    "non-denominational": "Non-Denominational",
    "non denominational": "Non-Denominational",
}


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = PHONE_DIGITS_RE.sub("", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return phone
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def normalize_denomination(denom: str | None) -> str | None:
    if not denom:
        return None
    key = denom.strip().lower()
    return DENOM_VOCAB.get(key, denom.strip().title())


def normalize_record(raw: RawChurchRecord) -> CleanChurchRecord | None:
    """Convert raw record into a clean normalized model."""
    name = clean_whitespace(raw.church_name)
    if not name:
        return None

    return CleanChurchRecord(
        record_id=raw.record_id,
        church_name=name,
        denomination=normalize_denomination(raw.denomination),
        website=canonical_website(raw.website),
        phone=normalize_phone(raw.phone),
        email=raw.email.lower().strip() if raw.email else None,
        street_address=clean_whitespace(raw.street_address),
        city=clean_whitespace(raw.city),
        state="FL",
        zip_code=clean_whitespace(raw.zip_code),
        county=clean_whitespace(raw.county),
        pastor_name=clean_whitespace(raw.pastor_name),
        service_times=clean_whitespace(raw.service_times),
        facebook_url=raw.facebook_url,
        instagram_url=raw.instagram_url,
        youtube_url=raw.youtube_url,
        latitude=raw.latitude,
        longitude=raw.longitude,
        source_url=raw.source_url,
        source_domain=raw.source_domain,
        scraped_at=raw.scraped_at,
        confidence_score=raw.confidence_score,
    )
