from __future__ import annotations

import re
import unicodedata

VARIANT_MAP = {
    "ministries": "ministry",
    "ctr": "center",
    "st": "saint",
    "mt": "mount",
    "assembly of god": "assembly",
    "church of god": "church",
    "incorporated": "inc",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for src, target in VARIANT_MAP.items():
        text = re.sub(rf"\b{re.escape(src)}\b", target, text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_zip(value: str | None) -> str:
    if not value:
        return ""
    m = re.search(r"\b(\d{5})", value)
    return m.group(1) if m else ""
