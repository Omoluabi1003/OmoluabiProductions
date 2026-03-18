"""Discovery query generation utilities."""

from __future__ import annotations

from typing import Iterable, List

DENOMINATION_HINTS = [
    "christian churches",
    "baptist church",
    "catholic church",
    "pentecostal church",
    "non denominational church",
    "methodist church",
]


def build_county_queries(county: str) -> List[str]:
    """Build county-level search queries."""
    return [
        f"churches in {county} county florida",
        f"church directory {county} county florida",
        f"best churches {county} county florida",
    ]


def build_city_queries(city: str) -> List[str]:
    """Build city-level denominational queries."""
    queries = [f"churches in {city} florida"]
    queries.extend(f"{hint} {city} florida" for hint in DENOMINATION_HINTS)
    return queries


def build_queries_for_county(county: str, cities: Iterable[str]) -> List[str]:
    """Aggregate county and city query strategy."""
    results = build_county_queries(county)
    for city in cities:
        results.extend(build_city_queries(city))
    return list(dict.fromkeys(results))
