"""CSV exports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from agent.models import CleanChurchRecord, DuplicateAuditRecord, RawChurchRecord


def export_raw(records: Iterable[RawChurchRecord], path: Path) -> None:
    rows = [r.model_dump(mode="json") for r in records]
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def export_clean(records: Iterable[CleanChurchRecord], path: Path) -> None:
    rows = [r.model_dump() for r in records]
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def export_duplicate_review(records: Iterable[DuplicateAuditRecord], path: Path) -> None:
    rows = [r.model_dump() for r in records]
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
