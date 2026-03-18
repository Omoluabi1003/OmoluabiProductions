"""HTTP fetching with retries and rate limiting."""

from __future__ import annotations

import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from agent.utils import safe_sleep

logger = logging.getLogger(__name__)


def build_session(user_agent: str, max_retries: int = 3) -> requests.Session:
    session = requests.Session()
    retry = Retry(total=max_retries, connect=max_retries, read=max_retries, backoff_factor=0.6)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": user_agent})
    return session


def fetch_url(
    session: requests.Session,
    url: str,
    timeout: int,
    min_delay: float,
    max_delay: float,
) -> Optional[str]:
    safe_sleep(min_delay, max_delay)
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None
