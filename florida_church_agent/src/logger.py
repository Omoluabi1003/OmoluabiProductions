"""Centralized logging setup."""

from __future__ import annotations

import logging
from pathlib import Path


def get_logger(log_path: Path) -> logging.Logger:
    """Create a console + file logger for scrape runs."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("florida_church_agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    return logger
