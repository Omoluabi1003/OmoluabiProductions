"""Normalization routines for church records."""

from __future__ import annotations

import re

from agent.cleaning.canonicalize import canonicalize_name, canonicalize_website
from agent.models import CleanChurchRecord, RawChurchRecord

DENOM_MAPPING = {
    "non denominational": "Nondenominational",
    "non-denominational": "Nondenominational",
    "baptist": "Baptist",
    "southern baptist": "Baptist",
    "catholic": "Catholic",
    "methodist": "Methodist",
    "pentecostal": "Pentecostal",
}


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone.strip()


def normalize_denomination(value: str) -> str:
    lowered = value.lower().strip()
    return DENOM_MAPPING.get(lowered, value.title() if value else "Unknown")


def normalize_state(state: str) -> str:
    return "FL" if state.strip().lower() in {"fl", "florida", ""} else state.strip().upper()


def normalize_record(raw: RawChurchRecord) -> CleanChurchRecord:
    return CleanChurchRecord(
        church_name=raw.church_name.strip(),
        canonical_name=canonicalize_name(raw.church_name),
        denomination=normalize_denomination(raw.denomination),
        website=canonicalize_website(raw.website),
        phone=normalize_phone(raw.phone),
        email=raw.email.strip().lower(),
        address=raw.address.strip(),
        city=raw.city.strip().title(),
        state=normalize_state(raw.state),
        zip=raw.zip.strip(),
        county=raw.county.strip(),
        pastor_name=raw.pastor_name.strip(),
        service_times=raw.service_times.strip(),
        facebook=raw.facebook.strip(),
        instagram=raw.instagram.strip(),
        youtube=raw.youtube.strip(),
        source_url=raw.source_url,
        source_type=raw.source_type,
        extraction_confidence=raw.extraction_confidence,
    )
