"""General utility functions."""

from __future__ import annotations

import random
import re
import time
from pathlib import Path
from urllib.parse import urlparse


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)


def safe_sleep(min_delay: float, max_delay: float) -> None:
    time.sleep(random.uniform(min_delay, max_delay))


def validate_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def safe_path(base: Path, candidate: Path) -> Path:
    resolved = (base / candidate).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise ValueError("Unsafe path traversal detected")
    return resolved
