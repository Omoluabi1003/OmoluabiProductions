"""Discovery pipeline for church and directory URLs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote_plus, urlparse

from bs4 import BeautifulSoup

from src.fetcher import PageFetcher
from src.query_builder import build_queries_for_county
from src.utils import extract_domain


@dataclass
class DiscoveredURL:
    url: str
    county: str
    city: str
    source_type: str


class SearchProvider:
    """Interface for web search providers."""

    def search(self, query: str) -> list[str]:
        raise NotImplementedError


class DuckDuckGoHtmlProvider(SearchProvider):
    """Public HTML search provider with no API key dependency.

    Note: selectors may require tuning as upstream markup changes.
    """

    def __init__(self, fetcher: PageFetcher):
        self.fetcher = fetcher

    def search(self, query: str) -> list[str]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        res = self.fetcher.fetch(url)
        if not res.text:
            return []
        soup = BeautifulSoup(res.text, "lxml")
        urls = []
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and href.startswith("http"):
                urls.append(href)
        return urls


def classify_domain(url: str) -> str:
    """Categorize discovered URLs for downstream priority."""
    domain = extract_domain(url) or ""
    church_keywords = ["church", "chapel", "cathedral", "ministry", "ministries"]
    directory_keywords = ["yelp", "yellowpages", "churchfinder", "faithstreet", "mapquest", "joinmychurch"]
    denom_keywords = ["sbc", "catholic", "umc", "ag", "episcopal", "pcusa"]

    if any(k in domain for k in church_keywords):
        return "official_church_domain"
    if any(k in domain for k in directory_keywords):
        return "directory_listing"
    if any(k in domain for k in denom_keywords):
        return "denominational_locator"
    return "miscellaneous"


class DiscoveryEngine:
    """Runs county/city query strategy and returns discovered URLs."""

    def __init__(self, search_provider: SearchProvider):
        self.search_provider = search_provider

    def discover(self, county: str, cities: Iterable[str]) -> list[DiscoveredURL]:
        discovered: list[DiscoveredURL] = []
        seen: set[str] = set()
        queries = build_queries_for_county(county, cities)

        for city in cities:
            for query in [q for q in queries if city.lower() in q.lower() or f"{county} county" in q.lower()]:
                urls = self.search_provider.search(query)
                for url in urls:
                    parsed = urlparse(url)
                    if not parsed.scheme.startswith("http"):
                        continue
                    key = f"{parsed.netloc}{parsed.path.rstrip('/')}"
                    if key in seen:
                        continue
                    seen.add(key)
                    discovered.append(
                        DiscoveredURL(
                            url=url,
                            county=county,
                            city=city,
                            source_type=classify_domain(url),
                        )
                    )
        return discovered
