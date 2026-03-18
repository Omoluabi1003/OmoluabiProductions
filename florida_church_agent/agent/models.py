"""Pydantic data models for church discovery pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class RawChurchRecord(BaseModel):
    church_name: str = ""
    denomination: str = ""
    website: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    state: str = "FL"
    zip: str = ""
    county: str = ""
    pastor_name: str = ""
    service_times: str = ""
    facebook: str = ""
    instagram: str = ""
    youtube: str = ""
    source_url: str
    source_type: str = "website"
    source_provider: str = "duckduckgo_html"
    source_query: str = ""
    extraction_confidence: float = 0.0
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CleanChurchRecord(BaseModel):
    church_name: str
    canonical_name: str
    denomination: str
    website: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    state: str = "FL"
    zip: str = ""
    county: str = ""
    pastor_name: str = ""
    service_times: str = ""
    facebook: str = ""
    instagram: str = ""
    youtube: str = ""
    source_url: str
    source_type: str
    extraction_confidence: float


class SourceAuditRecord(BaseModel):
    source_url: str
    provider: str
    query: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["discovered", "fetched", "failed", "parsed"] = "discovered"
    status_code: Optional[int] = None
    message: str = ""


class DuplicateAuditRecord(BaseModel):
    left_record_id: str
    right_record_id: str
    match_score: float
    dedupe_reason: str
    retained_record_id: str
    discarded_record_id: str


class RunSummary(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    counties_covered: int
    queries_executed: int
    urls_discovered: int
    urls_fetched: int
    records_raw: int
    records_clean: int
    duplicates_removed: int
    failures: int
    exports: list[str]
