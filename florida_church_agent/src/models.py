"""Pydantic models for raw and cleaned church records."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RawChurchRecord(BaseModel):
    """Raw extracted church record prior to normalization."""

    record_id: str
    church_name: Optional[str] = None
    denomination: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    county: Optional[str] = None
    pastor_name: Optional[str] = None
    service_times: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: str
    source_domain: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: Optional[str]) -> Optional[str]:
        return value.lower().strip() if value else value


class CleanChurchRecord(BaseModel):
    """Cleaned, normalized record ready for dedupe and export."""

    record_id: str
    church_name: str
    denomination: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: str = "FL"
    zip_code: Optional[str] = None
    county: Optional[str] = None
    pastor_name: Optional[str] = None
    service_times: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0


class SourceResult(BaseModel):
    """Tracks source-level scrape results for audit."""

    source_url: HttpUrl
    source_domain: str
    county: str
    fetched_ok: bool
    status_code: Optional[int] = None
    parser_used: Optional[str] = None
    records_extracted: int = 0
    error: Optional[str] = None


class ScrapeRunSummary(BaseModel):
    """Summary metrics for a run."""

    run_started_at: datetime
    run_finished_at: datetime
    total_discovered_urls: int
    total_fetched_urls: int
    total_failed_urls: int
    total_raw_records: int
    total_clean_records: int
    duplicates_flagged: int
    counties_processed: int
    notes: List[str] = Field(default_factory=list)
