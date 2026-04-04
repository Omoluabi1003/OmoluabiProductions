from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

SUNBIZ_KEYWORDS: List[str] = [
    "church",
    "ministry",
    "ministries",
    "temple",
    "fellowship",
    "worship",
    "cathedral",
    "tabernacle",
    "chapel",
    "assembly",
    "mission",
    "baptist",
    "apostolic",
    "presbyterian",
    "methodist",
    "pentecostal",
    "holiness",
    "catholic",
    "lutheran",
    "episcopal",
    "christian center",
    "community church",
]

MASTER_COLUMNS = [
    "Record ID", "Church Name", "Normalized Church Name", "Source Systems",
    "Florida Registered Entity", "Sunbiz Entity Name", "Sunbiz Document Number",
    "Sunbiz Status", "Sunbiz Entity Type", "Sunbiz Filing Date", "Sunbiz Principal Address",
    "Sunbiz Mailing Address", "IRS Organization Name", "IRS EIN", "IRS Subsection Code",
    "IRS Foundation Code", "IRS Ruling Date", "IRS Deductibility Status", "IRS Revocation Status",
    "IRS City", "IRS State", "OSM Name", "Denomination", "Religion", "Street Address", "City",
    "County", "State", "ZIP Code", "Latitude", "Longitude", "Geocode Source",
    "Match Confidence Score", "Duplicate Flag", "Review Status", "Notes", "Raw Source URLs",
]

DATA_DICTIONARY_ROWS = [
    ("Record ID", "Unique internal ID for each final row", "Pipeline", "FLCH-000001"),
    ("Church Name", "Best display name after reconciliation", "Matched sources", "First Baptist Church"),
    ("Normalized Church Name", "Standardized name for matching", "Pipeline", "first baptist church"),
    ("Source Systems", "Comma-separated list of source systems that contributed", "Pipeline", "Sunbiz, IRS"),
    ("Florida Registered Entity", "Yes if a Sunbiz entity match exists", "Sunbiz", "Yes"),
    ("Raw Source URLs", "Semicolon-separated source URLs used for this record", "All", "https://...;https://..."),
]


@dataclass
class PipelineConfig:
    output_dir: Path = Path("./output")
    timeout_seconds: int = 60
    retries: int = 3
    rate_limit_seconds: float = 0.35
    irs_bulk_file: Path | None = None
    user_agent: str = "FloridaChurchesPipeline/1.0 (contact: data-team@example.org)"
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    sunbiz_base: str = "https://search.sunbiz.org/Inquiry/CorporationSearch"
    log_file_name: str = "Florida_Churches_Run_Log.txt"
    keyword_list: List[str] = field(default_factory=lambda: SUNBIZ_KEYWORDS.copy())
