from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from math import radians, cos, sin, asin, sqrt

from transform.normalize import normalize_text, normalize_zip


@dataclass
class Candidate:
    name: str
    normalized_name: str
    city: str
    zip_code: str
    latitude: float | None
    longitude: float | None


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 3956 * c


def confidence_score(base: Candidate, other: Candidate) -> int:
    score = 0.0
    if base.normalized_name and base.normalized_name == other.normalized_name:
        score += 55
    else:
        score += _ratio(base.normalized_name, other.normalized_name) * 45

    if base.city and other.city and normalize_text(base.city) == normalize_text(other.city):
        score += 15

    if base.zip_code and other.zip_code and normalize_zip(base.zip_code) == normalize_zip(other.zip_code):
        score += 10

    if all(v is not None for v in [base.latitude, base.longitude, other.latitude, other.longitude]):
        miles = haversine_miles(base.latitude, base.longitude, other.latitude, other.longitude)
        if miles <= 0.3:
            score += 20
        elif miles <= 1:
            score += 12
        elif miles <= 3:
            score += 6

    return max(0, min(100, round(score)))
