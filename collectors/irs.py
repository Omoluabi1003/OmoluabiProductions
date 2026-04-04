from __future__ import annotations

import csv
import logging
from pathlib import Path

from config import PipelineConfig
from transform.normalize import normalize_text

KEYWORDS = [
    "church", "ministry", "ministries", "temple", "fellowship", "worship",
    "cathedral", "tabernacle", "chapel", "assembly", "mission", "baptist",
    "apostolic", "presbyterian", "methodist", "pentecostal", "holiness",
    "catholic", "lutheran", "episcopal", "christian center", "community church",
]


def _is_likely_church(name: str) -> bool:
    n = normalize_text(name)
    return any(k in n for k in KEYWORDS)


def _detect(colnames: list[str], *options: str) -> str:
    lower = {c.lower(): c for c in colnames}
    for opt in options:
        if opt.lower() in lower:
            return lower[opt.lower()]
    return ""


def collect_irs(config: PipelineConfig) -> list[dict]:
    log = logging.getLogger(__name__)
    if not config.irs_bulk_file:
        log.warning("No IRS bulk file configured; IRS raw export will be empty.")
        return []

    src = Path(config.irs_bulk_file)
    if not src.exists():
        log.warning("IRS bulk file not found: %s", src)
        return []

    rows = []
    with src.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fnames = reader.fieldnames or []

        org_col = _detect(fnames, "name", "organization_name", "TAXPAYER_NAME")
        ein_col = _detect(fnames, "ein", "EIN")
        sub_col = _detect(fnames, "subsection_code", "SUBSECTION_CODE")
        found_col = _detect(fnames, "foundation_code", "FOUNDATION_CODE")
        ruling_col = _detect(fnames, "ruling_date", "RULING_DATE")
        city_col = _detect(fnames, "city", "CITY")
        state_col = _detect(fnames, "state", "STATE")
        ded_col = _detect(fnames, "deductibility_status", "DEDUCTIBILITY_CD")
        rev_col = _detect(fnames, "revocation_status", "REVOCATION_DATE")

        for row in reader:
            org = (row.get(org_col) or "").strip()
            state = (row.get(state_col) or "").strip().upper()
            if state != "FL" or not org or not _is_likely_church(org):
                continue
            rows.append(
                {
                    "organization_name": org,
                    "ein": (row.get(ein_col) or "").strip(),
                    "subsection_code": (row.get(sub_col) or "").strip(),
                    "foundation_code": (row.get(found_col) or "").strip(),
                    "ruling_date": (row.get(ruling_col) or "").strip(),
                    "deductibility_status": (row.get(ded_col) or "").strip(),
                    "revocation_status": "Revoked" if (row.get(rev_col) or "").strip() else "Not Revoked",
                    "city": (row.get(city_col) or "").strip(),
                    "state": state,
                    "source_url": str(src.resolve()),
                }
            )

    rows.sort(key=lambda r: (r["organization_name"], r["ein"]))
    return rows
