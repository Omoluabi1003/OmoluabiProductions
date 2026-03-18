"""DuckDuckGo HTML discovery provider."""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .providers import DiscoveryProvider, SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoHTMLProvider(DiscoveryProvider):
    provider_name = "duckduckgo_html"

    def __init__(self, session: requests.Session, timeout: int = 20) -> None:
        self.session = session
        self.timeout = timeout

    def search(self, query: str, max_results: int = 20) -> list[SearchResult]:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[SearchResult] = []
        for node in soup.select(".result")[:max_results]:
            link = node.select_one(".result__a")
            if not link:
                continue
            snippet_node = node.select_one(".result__snippet")
            results.append(
                SearchResult(
                    provider=self.provider_name,
                    query=query,
                    url=link.get("href", ""),
                    title=link.get_text(strip=True),
                    snippet=snippet_node.get_text(" ", strip=True) if snippet_node else "",
                )
            )
        logger.debug("Provider %s discovered %s results for query %s", self.provider_name, len(results), query)
        return results
