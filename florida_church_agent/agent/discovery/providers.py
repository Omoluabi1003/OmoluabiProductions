"""Provider abstraction for URL discovery."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class SearchResult:
    provider: str
    query: str
    url: str
    title: str = ""
    snippet: str = ""
    discovered_at: datetime = datetime.now(timezone.utc)


class DiscoveryProvider(ABC):
    provider_name: str

    @abstractmethod
    def search(self, query: str, max_results: int = 20) -> list[SearchResult]:
        raise NotImplementedError
