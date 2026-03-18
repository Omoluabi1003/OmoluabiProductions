"""Configuration loading for the Florida Church Discovery Agent."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Runtime configuration for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Florida Church Discovery Agent"
    company_name: str = "ETL GIS Consulting LLC"
    environment: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    safe_mode: bool = True
    request_timeout_seconds: int = 20
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 2.5
    max_retries: int = 3
    default_max_pages: int = 5000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FloridaChurchAgent/1.0"
    sqlite_path: Path = Path("data/logs/church_agent.db")
    raw_export_path: Path = Path("data/raw/churches_florida_raw.csv")
    clean_export_path: Path = Path("data/cleaned/churches_florida_cleaned.csv")
    excel_export_path: Path = Path("data/cleaned/churches_florida.xlsx")
    failed_urls_path: Path = Path("data/logs/failed_urls.csv")
    source_summary_path: Path = Path("data/logs/source_summary.csv")
    duplicate_review_path: Path = Path("data/logs/duplicate_review.csv")
    run_summary_path: Path = Path("data/logs/run_summary.json")
    scrape_log_path: Path = Path("data/logs/scrape_log.txt")
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8098
    playwright_enabled: bool = False

    @property
    def project_root(self) -> Path:
        """Return the application root path and support PyInstaller bundles."""
        if hasattr(os, "_MEIPASS"):
            return Path(getattr(os, "_MEIPASS"))
        return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and cache environment configuration."""
    load_dotenv(override=False)
    cfg = AppConfig()
    for path in (
        cfg.sqlite_path,
        cfg.raw_export_path,
        cfg.clean_export_path,
        cfg.excel_export_path,
        cfg.failed_urls_path,
        cfg.source_summary_path,
        cfg.duplicate_review_path,
        cfg.run_summary_path,
        cfg.scrape_log_path,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
    return cfg
