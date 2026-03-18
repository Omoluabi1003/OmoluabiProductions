"""HTTP fetcher with retries, rate limiting, and robots policy checks."""

from __future__ import annotations

from dataclasses import dataclass
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from src.utils import random_user_agent, sleep_with_rate_limit


@dataclass
class FetchResult:
    url: str
    status_code: int | None
    text: str
    error: str | None = None


class PageFetcher:
    """Polite HTTP client for scraping publicly accessible pages."""

    def __init__(self) -> None:
        self.session = requests.Session()

    def _is_allowed(self, url: str, user_agent: str = "*") -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(user_agent, url)
        except Exception:
            return True

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=8), reraise=True)
    def _request(self, url: str) -> requests.Response:
        headers = {"User-Agent": random_user_agent(settings.user_agent_rotation)}
        return self.session.get(url, headers=headers, timeout=settings.request_timeout, allow_redirects=True)

    def fetch(self, url: str) -> FetchResult:
        sleep_with_rate_limit(settings.rate_limit_seconds)
        ua = random_user_agent(settings.user_agent_rotation)
        if not self._is_allowed(url, ua):
            return FetchResult(url=url, status_code=None, text="", error="Blocked by robots.txt")
        try:
            response = self._request(url)
            return FetchResult(url=url, status_code=response.status_code, text=response.text)
        except Exception as exc:
            return FetchResult(url=url, status_code=None, text="", error=str(exc))

    @staticmethod
    def absolute_url(base_url: str, href: str) -> str:
        return urljoin(base_url, href)
