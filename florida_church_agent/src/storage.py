"""SQLite storage layer for checkpoint/resume and audit trails."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable


class Storage:
    """Persistence utility for crawl state and outputs."""

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS discovered_urls (
                url TEXT PRIMARY KEY,
                county TEXT,
                city TEXT,
                source_type TEXT,
                status TEXT DEFAULT 'pending',
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS fetched_pages (
                url TEXT PRIMARY KEY,
                status_code INTEGER,
                success INTEGER,
                parser_used TEXT,
                fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                error TEXT
            );

            CREATE TABLE IF NOT EXISTS raw_records (
                record_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS clean_records (
                record_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS run_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        self.conn.commit()

    def upsert_discovered_url(self, url: str, county: str, city: str, source_type: str) -> None:
        self.conn.execute(
            """
            INSERT INTO discovered_urls(url, county, city, source_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(url) DO NOTHING
            """,
            (url, county, city, source_type),
        )
        self.conn.commit()

    def pending_urls(self, limit: int) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT * FROM discovered_urls WHERE status='pending' LIMIT ?",
            (limit,),
        )
        return cur.fetchall()

    def mark_url_status(self, url: str, status: str) -> None:
        self.conn.execute("UPDATE discovered_urls SET status=? WHERE url=?", (status, url))
        self.conn.commit()

    def save_fetched_page(self, url: str, status_code: int | None, success: bool, parser_used: str, error: str | None) -> None:
        self.conn.execute(
            """
            INSERT INTO fetched_pages(url, status_code, success, parser_used, error)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                status_code=excluded.status_code,
                success=excluded.success,
                parser_used=excluded.parser_used,
                error=excluded.error,
                fetched_at=CURRENT_TIMESTAMP
            """,
            (url, status_code, int(success), parser_used, error),
        )
        self.conn.commit()

    def save_records(self, table: str, records: Iterable[dict[str, Any]]) -> None:
        for record in records:
            self.conn.execute(
                f"""
                INSERT INTO {table}(record_id, payload)
                VALUES (?, ?)
                ON CONFLICT(record_id) DO UPDATE SET payload=excluded.payload
                """,
                (record["record_id"], json.dumps(record, default=str)),
            )
        self.conn.commit()

    def read_records(self, table: str) -> list[dict[str, Any]]:
        cur = self.conn.execute(f"SELECT payload FROM {table}")
        return [json.loads(row["payload"]) for row in cur.fetchall()]

    def set_state(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO run_state(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    def get_state(self, key: str, default: str = "") -> str:
        cur = self.conn.execute("SELECT value FROM run_state WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def close(self) -> None:
        self.conn.close()
