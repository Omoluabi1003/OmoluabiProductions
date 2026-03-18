"""Build layered discovery queries for Florida counties."""

from __future__ import annotations

COUNTIES_FL = [
    "Alachua", "Baker", "Bay", "Bradford", "Brevard", "Broward", "Calhoun", "Charlotte", "Citrus",
    "Clay", "Collier", "Columbia", "DeSoto", "Dixie", "Duval", "Escambia", "Flagler", "Franklin",
    "Gadsden", "Gilchrist", "Glades", "Gulf", "Hamilton", "Hardee", "Hendry", "Hernando", "Highlands",
    "Hillsborough", "Holmes", "Indian River", "Jackson", "Jefferson", "Lafayette", "Lake", "Lee", "Leon",
    "Levy", "Liberty", "Madison", "Manatee", "Marion", "Martin", "Miami-Dade", "Monroe", "Nassau",
    "Okaloosa", "Okeechobee", "Orange", "Osceola", "Palm Beach", "Pasco", "Pinellas", "Polk", "Putnam",
    "Santa Rosa", "Sarasota", "Seminole", "St. Johns", "St. Lucie", "Sumter", "Suwannee", "Taylor", "Union",
    "Volusia", "Wakulla", "Walton", "Washington",
]

CITY_HINTS = {
    "Miami-Dade": ["Miami", "Hialeah"],
    "Orange": ["Orlando"],
    "Hillsborough": ["Tampa"],
    "Duval": ["Jacksonville"],
}

TERMS = [
    "church",
    "christian church",
    "baptist church",
    "pentecostal church",
    "catholic church",
    "methodist church",
    "nondenominational church",
    "worship center",
]


def build_queries(state: str = "Florida") -> list[tuple[str, str]]:
    """Return (county, query) tuples for provider searches."""
    queries: list[tuple[str, str]] = []
    for county in COUNTIES_FL:
        county_phrase = f"{county} County"
        for term in TERMS:
            queries.append((county, f'{term} "{county_phrase}" {state}'))
        for city in CITY_HINTS.get(county, []):
            for term in TERMS:
                queries.append((county, f'{term} "{city}" {state}'))
    return queries
