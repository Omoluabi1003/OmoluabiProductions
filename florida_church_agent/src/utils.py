"""General helper functions."""

from __future__ import annotations

import random
import re
import time
from urllib.parse import urlparse


def sleep_with_rate_limit(seconds: float) -> None:
    """Polite request pacing."""
    time.sleep(max(seconds, 0))


def random_user_agent(user_agents: list[str]) -> str:
    """Pick a user-agent from configured rotation."""
    return random.choice(user_agents)


def clean_whitespace(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip()


def extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    return urlparse(url).netloc.lower().replace("www.", "")


def canonical_website(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    domain = parsed.netloc or parsed.path
    if not domain:
        return None
    return f"{scheme}://{domain.lower().replace('www.', '')}"
