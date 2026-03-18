"""Centralized logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_path: Path, log_level: str = "INFO") -> None:
    """Configure console and file logging without leaking secrets."""
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(log_level.upper())
    root.handlers.clear()

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(formatter)

    root.addHandler(sh)
    root.addHandler(fh)
