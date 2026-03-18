"""Best-effort robots.txt check."""

from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


_cache: dict[str, RobotFileParser] = {}


def can_fetch(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in _cache:
        rp = RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        try:
            rp.read()
        except Exception:
            return True
        _cache[base] = rp
    return _cache[base].can_fetch(user_agent, url)
