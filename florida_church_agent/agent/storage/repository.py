"""Repository helpers around checkpoint storage."""

from __future__ import annotations

from datetime import datetime, timezone

from agent.models import CleanChurchRecord, SourceAuditRecord
from agent.storage.checkpoint_db import CheckpointDB


class Repository:
    def __init__(self, checkpoint_db: CheckpointDB) -> None:
        self.db = checkpoint_db

    def save_discovered_url(self, url: str, county: str, query: str, provider: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO discovered_urls(url, county, query, provider, discovered_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (url, county, query, provider, now),
            )

    def discovered_urls(self) -> list[str]:
        with self.db.connection() as conn:
            cur = conn.execute("SELECT url FROM discovered_urls")
            return [row[0] for row in cur.fetchall()]

    def set_fetch_status(self, audit: SourceAuditRecord) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO fetch_status(url, status, status_code, message, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    status=excluded.status,
                    status_code=excluded.status_code,
                    message=excluded.message,
                    updated_at=excluded.updated_at
                """,
                (
                    audit.source_url,
                    audit.status,
                    audit.status_code,
                    audit.message,
                    audit.fetched_at.isoformat(),
                ),
            )

    def save_clean_record(self, record: CleanChurchRecord) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO parsed_records(canonical_name, payload_json, source_url) VALUES (?, ?, ?)",
                (record.canonical_name, record.model_dump_json(), record.source_url),
            )

    def mark_export(self, artifact: str) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO exports(artifact, exported_at) VALUES (?, datetime('now'))",
                (artifact,),
            )
