"""CLI entry point for Florida Church Discovery Agent."""

from __future__ import annotations

import argparse
import json
import logging
import uuid
from datetime import datetime, timezone

from agent.cleaning.classify import classify_source
from agent.cleaning.dedupe import dedupe_records
from agent.cleaning.normalize import normalize_record
from agent.config import get_config
from agent.dashboard.server import create_app
from agent.discovery.duckduckgo_html import DuckDuckGoHTMLProvider
from agent.discovery.query_builder import COUNTIES_FL, build_queries
from agent.export.csv_exporter import export_clean, export_duplicate_review, export_raw
from agent.export.excel_exporter import export_excel
from agent.export.run_summary import write_run_summary
from agent.logging_config import configure_logging
from agent.models import RunSummary, SourceAuditRecord
from agent.scraping.extractor import extract_record
from agent.scraping.fetcher import build_session, fetch_url
from agent.scraping.playwright_fallback import fetch_with_playwright
from agent.scraping.robots import can_fetch
from agent.storage.checkpoint_db import CheckpointDB
from agent.storage.repository import Repository

logger = logging.getLogger(__name__)


def run_pipeline(state: str, max_pages: int, use_playwright: bool, exports: set[str]) -> RunSummary:
    config = get_config()
    configure_logging(config.scrape_log_path, config.log_level)
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    session = build_session(config.user_agent, config.max_retries)
    provider = DuckDuckGoHTMLProvider(session=session, timeout=config.request_timeout_seconds)
    repo = Repository(CheckpointDB(config.sqlite_path))

    raw_records = []
    clean_records = []
    failures: list[dict[str, str]] = []
    discovered_count = 0
    fetched_count = 0
    query_count = 0

    for county, query in build_queries(state=state):
        query_count += 1
        try:
            results = provider.search(query, max_results=12)
        except Exception as exc:
            logger.warning("Search failed for %s: %s", query, exc)
            continue

        for result in results:
            if discovered_count >= max_pages:
                break
            repo.save_discovered_url(result.url, county, query, result.provider)
            discovered_count += 1

            if not can_fetch(result.url, config.user_agent):
                continue
            html = fetch_url(
                session,
                result.url,
                config.request_timeout_seconds,
                config.min_delay_seconds if config.safe_mode else 0.2,
                config.max_delay_seconds if config.safe_mode else 0.8,
            )
            if html is None and use_playwright:
                import asyncio

                html = asyncio.run(fetch_with_playwright(result.url))
            if html is None:
                failures.append({"url": result.url, "reason": "fetch_failed"})
                repo.set_fetch_status(
                    SourceAuditRecord(
                        source_url=result.url,
                        provider=result.provider,
                        query=query,
                        status="failed",
                        message="fetch_failed",
                    )
                )
                continue

            fetched_count += 1
            raw = extract_record(result.url, html, county=county, query=query, provider=result.provider)
            raw.source_type = classify_source(raw.source_url)
            raw_records.append(raw)
            clean = normalize_record(raw)
            clean_records.append(clean)
            repo.save_clean_record(clean)
            repo.set_fetch_status(
                SourceAuditRecord(
                    source_url=result.url,
                    provider=result.provider,
                    query=query,
                    status="parsed",
                    status_code=200,
                )
            )

        if discovered_count >= max_pages:
            break

    unique_records, dupes = dedupe_records(clean_records)
    export_paths: list[str] = []

    export_raw(raw_records, config.raw_export_path)
    export_paths.append(str(config.raw_export_path))
    repo.mark_export(str(config.raw_export_path))

    if "csv" in exports:
        export_clean(unique_records, config.clean_export_path)
        export_paths.append(str(config.clean_export_path))
        repo.mark_export(str(config.clean_export_path))

    if "excel" in exports:
        export_excel(unique_records, config.excel_export_path)
        export_paths.append(str(config.excel_export_path))
        repo.mark_export(str(config.excel_export_path))

    export_duplicate_review(dupes, config.duplicate_review_path)
    export_paths.append(str(config.duplicate_review_path))

    if failures:
        import csv

        with config.failed_urls_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["url", "reason"])
            w.writeheader()
            w.writerows(failures)

    summary = RunSummary(
        run_id=run_id,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        counties_covered=len(COUNTIES_FL),
        queries_executed=query_count,
        urls_discovered=discovered_count,
        urls_fetched=fetched_count,
        records_raw=len(raw_records),
        records_clean=len(unique_records),
        duplicates_removed=len(dupes),
        failures=len(failures),
        exports=export_paths,
    )
    write_run_summary(summary, config.run_summary_path)
    config.source_summary_path.write_text(
        "source_type,count\n" + "\n".join(
            f"{stype},{sum(1 for r in raw_records if r.source_type == stype)}"
            for stype in sorted(set(r.source_type for r in raw_records))
        ),
        encoding="utf-8",
    )

    return summary


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Florida Church Discovery Agent")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Start a new run")
    run_p.add_argument("--state", default="Florida")
    run_p.add_argument("--max-pages", type=int, default=get_config().default_max_pages)
    run_p.add_argument("--use-playwright", action="store_true")
    run_p.add_argument("--export", choices=["csv", "excel"], action="append", default=["csv", "excel"])

    sub.add_parser("resume", help="Resume from current checkpoint")
    sub.add_parser("summary", help="Print latest summary")
    sub.add_parser("counties", help="Print Florida counties")
    sub.add_parser("serve-dashboard", help="Run local monitoring dashboard")
    return parser


def main() -> None:
    args = create_parser().parse_args()
    config = get_config()

    if args.command == "counties":
        for county in COUNTIES_FL:
            print(county)
        return

    if args.command == "summary":
        if config.run_summary_path.exists():
            print(config.run_summary_path.read_text(encoding="utf-8"))
        else:
            print("No summary found")
        return

    if args.command == "serve-dashboard":
        app = create_app(config)
        app.run(host=config.dashboard_host, port=config.dashboard_port, debug=False)
        return

    if args.command in {"run", "resume"}:
        summary = run_pipeline(
            state=getattr(args, "state", "Florida"),
            max_pages=getattr(args, "max_pages", config.default_max_pages),
            use_playwright=getattr(args, "use_playwright", False) or config.playwright_enabled,
            exports=set(getattr(args, "export", ["csv", "excel"])),
        )
        print(json.dumps(summary.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
