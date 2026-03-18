"""Configuration management for Florida Church Agent."""

from __future__ import annotations

from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8")

    request_timeout: int = Field(default=20, alias="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    rate_limit_seconds: float = Field(default=1.0, alias="RATE_LIMIT_SECONDS")
    max_pages: int = Field(default=5000, alias="MAX_PAGES")
    use_playwright: bool = Field(default=False, alias="USE_PLAYWRIGHT")
    enable_geocoding: bool = Field(default=False, alias="ENABLE_GEOCODING")
    geocode_provider: str = Field(default="nominatim", alias="GEOCODE_PROVIDER")

    # Optional API keys
    positionstack_api_key: str = Field(default="", alias="POSITIONSTACK_API_KEY")
    google_geocoding_api_key: str = Field(default="", alias="GOOGLE_GEOCODING_API_KEY")
    mapbox_api_key: str = Field(default="", alias="MAPBOX_API_KEY")

    fuzzy_dup_threshold: int = Field(default=88, alias="FUZZY_DUP_THRESHOLD")
    user_agent_rotation: List[str] = Field(
        default_factory=lambda: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ],
        alias="USER_AGENT_ROTATION",
    )
    output_dir: str = Field(default=str(BASE_DIR / "data"), alias="OUTPUT_DIR")
    sqlite_db_path: str = Field(default=str(BASE_DIR / "cache" / "church_agent.db"), alias="SQLITE_DB_PATH")


settings = Settings()
