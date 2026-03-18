"""SQLite checkpointing and audit persistence."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS discovered_urls (
    url TEXT PRIMARY KEY,
    county TEXT,
    query TEXT,
    provider TEXT,
    discovered_at TEXT
);
CREATE TABLE IF NOT EXISTS fetch_status (
    url TEXT PRIMARY KEY,
    status TEXT,
    status_code INTEGER,
    message TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS parsed_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT,
    payload_json TEXT,
    source_url TEXT
);
CREATE TABLE IF NOT EXISTS exports (
    artifact TEXT PRIMARY KEY,
    exported_at TEXT
);
"""


class CheckpointDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
