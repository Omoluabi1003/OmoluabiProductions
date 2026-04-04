from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from collectors.irs import collect_irs
from collectors.osm import collect_osm
from collectors.sunbiz import collect_sunbiz
from config import DATA_DICTIONARY_ROWS, MASTER_COLUMNS, PipelineConfig
from export.write_excel import write_workbook
from transform.match import Candidate, confidence_score
from transform.normalize import normalize_text


def setup_logging(output_dir: Path, log_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / log_name
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )


def _build_master(sunbiz: list[dict], irs: list[dict], osm: list[dict]) -> pd.DataFrame:
    sunbiz_by_norm = {}
    for row in sunbiz:
        n = normalize_text(row.get("entity_name", ""))
        sunbiz_by_norm.setdefault(n, []).append(row)

    irs_by_norm = {}
    for row in irs:
        n = normalize_text(row.get("organization_name", ""))
        irs_by_norm.setdefault(n, []).append(row)

    all_names = sorted({k for k in sunbiz_by_norm} | {k for k in irs_by_norm} | {normalize_text(o.get('name', '')) for o in osm if o.get('name')})

    master_rows = []
    for i, norm_name in enumerate(all_names, start=1):
        s_rec = (sunbiz_by_norm.get(norm_name) or [None])[0]
        i_rec = (irs_by_norm.get(norm_name) or [None])[0]

        best_osm = None
        best_score = 0
        base = Candidate(
            name=(s_rec or i_rec or {}).get("entity_name") or (s_rec or i_rec or {}).get("organization_name") or "",
            normalized_name=norm_name,
            city=(i_rec or {}).get("city", ""),
            zip_code="",
            latitude=None,
            longitude=None,
        )
        for o in osm:
            c = Candidate(
                name=o.get("name", ""),
                normalized_name=normalize_text(o.get("name", "")),
                city=o.get("city", ""),
                zip_code=o.get("postcode", ""),
                latitude=o.get("latitude"),
                longitude=o.get("longitude"),
            )
            score = confidence_score(base, c)
            if score > best_score:
                best_score = score
                best_osm = o

        source_systems = []
        if s_rec:
            source_systems.append("Sunbiz")
        if i_rec:
            source_systems.append("IRS")
        if best_osm and best_score >= 60:
            source_systems.append("OSM")

        duplicate_flag = "No"
        review_status = "Matched"
        notes = ""
        if best_score < 70 and (best_osm is not None):
            review_status = "Needs Review"
            notes = "Low-confidence OSM linkage"
        if not s_rec and not i_rec:
            review_status = "Unmatched"

        church_name = (s_rec or {}).get("entity_name") or (i_rec or {}).get("organization_name") or (best_osm or {}).get("name", "")
        raw_urls = [
            (s_rec or {}).get("source_url", ""),
            (i_rec or {}).get("source_url", ""),
            (best_osm or {}).get("source_url", "") if best_osm and best_score >= 60 else "",
        ]
        raw_urls = [u for u in raw_urls if u]

        master_rows.append(
            {
                "Record ID": f"FLCH-{i:06d}",
                "Church Name": church_name,
                "Normalized Church Name": norm_name,
                "Source Systems": ", ".join(source_systems),
                "Florida Registered Entity": "Yes" if s_rec else "No",
                "Sunbiz Entity Name": (s_rec or {}).get("entity_name", ""),
                "Sunbiz Document Number": (s_rec or {}).get("document_number", ""),
                "Sunbiz Status": (s_rec or {}).get("status", ""),
                "Sunbiz Entity Type": (s_rec or {}).get("entity_type", ""),
                "Sunbiz Filing Date": (s_rec or {}).get("filing_date", ""),
                "Sunbiz Principal Address": (s_rec or {}).get("principal_address", ""),
                "Sunbiz Mailing Address": (s_rec or {}).get("mailing_address", ""),
                "IRS Organization Name": (i_rec or {}).get("organization_name", ""),
                "IRS EIN": (i_rec or {}).get("ein", ""),
                "IRS Subsection Code": (i_rec or {}).get("subsection_code", ""),
                "IRS Foundation Code": (i_rec or {}).get("foundation_code", ""),
                "IRS Ruling Date": (i_rec or {}).get("ruling_date", ""),
                "IRS Deductibility Status": (i_rec or {}).get("deductibility_status", ""),
                "IRS Revocation Status": (i_rec or {}).get("revocation_status", ""),
                "IRS City": (i_rec or {}).get("city", ""),
                "IRS State": (i_rec or {}).get("state", ""),
                "OSM Name": (best_osm or {}).get("name", "") if best_osm and best_score >= 60 else "",
                "Denomination": (best_osm or {}).get("denomination", "") if best_osm and best_score >= 60 else "",
                "Religion": (best_osm or {}).get("religion", "") if best_osm and best_score >= 60 else "",
                "Street Address": (best_osm or {}).get("street", "") if best_osm and best_score >= 60 else "",
                "City": (best_osm or {}).get("city", "") if best_osm and best_score >= 60 else (i_rec or {}).get("city", ""),
                "County": "",
                "State": (best_osm or {}).get("state", "") if best_osm and best_score >= 60 else (i_rec or {}).get("state", ""),
                "ZIP Code": (best_osm or {}).get("postcode", "") if best_osm and best_score >= 60 else "",
                "Latitude": (best_osm or {}).get("latitude", "") if best_osm and best_score >= 60 else "",
                "Longitude": (best_osm or {}).get("longitude", "") if best_osm and best_score >= 60 else "",
                "Geocode Source": "OSM" if best_osm and best_score >= 60 else "",
                "Match Confidence Score": best_score if best_osm else (100 if s_rec and i_rec else 0),
                "Duplicate Flag": duplicate_flag,
                "Review Status": review_status,
                "Notes": notes,
                "Raw Source URLs": ";".join(raw_urls),
            }
        )

    master = pd.DataFrame(master_rows)
    if master.empty:
        master = pd.DataFrame(columns=MASTER_COLUMNS)
    else:
        master = master[MASTER_COLUMNS]

    dupes = master[master["Normalized Church Name"].duplicated(keep=False)].copy()
    if not dupes.empty:
        master.loc[dupes.index, "Duplicate Flag"] = "Yes"
        master.loc[dupes.index, "Review Status"] = "Duplicate Candidate"

    master = master.sort_values(["Normalized Church Name", "Record ID"]).reset_index(drop=True)
    return master


def run_pipeline(args: argparse.Namespace) -> None:
    config = PipelineConfig(output_dir=Path(args.output), irs_bulk_file=Path(args.irs_bulk_file) if args.irs_bulk_file else None)
    setup_logging(config.output_dir, config.log_file_name)

    logging.info("Starting pipeline")
    sunbiz_rows = collect_sunbiz(config, config.keyword_list) if args.run_all or args.sunbiz_only else []
    irs_rows = collect_irs(config) if args.run_all or args.irs_only else []
    osm_rows = collect_osm(config) if args.run_all or args.osm_only else []

    sunbiz_df = pd.DataFrame(sunbiz_rows)
    irs_df = pd.DataFrame(irs_rows)
    osm_df = pd.DataFrame(osm_rows)

    if args.run_all:
        master = _build_master(sunbiz_rows, irs_rows, osm_rows)
    else:
        master = pd.DataFrame(columns=MASTER_COLUMNS)

    duplicate_review = master[master["Duplicate Flag"] == "Yes"].copy() if not master.empty else pd.DataFrame(columns=MASTER_COLUMNS)
    unmatched_review = master[master["Review Status"].isin(["Unmatched", "Needs Review"])].copy() if not master.empty else pd.DataFrame(columns=MASTER_COLUMNS)

    data_dictionary = pd.DataFrame(DATA_DICTIONARY_ROWS, columns=["Column Name", "Description", "Source", "Example Value"])

    out = config.output_dir
    out.mkdir(parents=True, exist_ok=True)

    master.to_csv(out / "Florida_Churches_Master.csv", index=False)
    sunbiz_df.to_csv(out / "Florida_Churches_Sunbiz_Raw.csv", index=False)
    irs_df.to_csv(out / "Florida_Churches_IRS_Raw.csv", index=False)
    osm_df.to_csv(out / "Florida_Churches_OSM_Raw.csv", index=False)

    write_workbook(
        out / "Florida_Churches_Master.xlsx",
        master,
        sunbiz_df,
        irs_df,
        osm_df,
        duplicate_review,
        unmatched_review,
        data_dictionary,
    )
    duplicate_review.to_excel(out / "Florida_Churches_Duplicate_Review.xlsx", index=False)
    unmatched_review.to_excel(out / "Florida_Churches_Unmatched_Review.xlsx", index=False)

    logging.info("Pipeline complete: %s", out.resolve())


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Florida Churches data pipeline")
    p.add_argument("--run-all", action="store_true")
    p.add_argument("--sunbiz-only", action="store_true")
    p.add_argument("--irs-only", action="store_true")
    p.add_argument("--osm-only", action="store_true")
    p.add_argument("--output", default="./output")
    p.add_argument("--irs-bulk-file", default="")
    return p


if __name__ == "__main__":
    parser = build_parser()
    ns = parser.parse_args()
    if not any([ns.run_all, ns.sunbiz_only, ns.irs_only, ns.osm_only]):
        parser.error("One mode required: --run-all/--sunbiz-only/--irs-only/--osm-only")
    run_pipeline(ns)
