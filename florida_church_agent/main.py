"""CLI entrypoint for Florida church scraping pipeline."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from tqdm import tqdm

from config import settings
from src.counties import COUNTY_TO_CITIES, FLORIDA_COUNTIES, get_cities_for_county
from src.deduplicate import deduplicate_records
from src.discover import DiscoveryEngine, DuckDuckGoHtmlProvider
from src.exporter import export_clean_csv, export_excel, export_logs, export_raw_csv
from src.extractors import extract_church_record
from src.fetcher import PageFetcher
from src.geocode import geocode_address
from src.logger import get_logger
from src.models import CleanChurchRecord, RawChurchRecord, ScrapeRunSummary, SourceResult
from src.normalize import normalize_record
from src.parsers import parse_html, relevant_subpage_links
from src.playwright_fetcher import PlaywrightFetcher
from src.storage import Storage

app = typer.Typer(help="Florida Church Agent CLI")


def _paths() -> dict[str, Path]:
    output = Path(settings.output_dir)
    return {
        "raw_csv": output / "raw" / "churches_florida_raw.csv",
        "clean_csv": output / "cleaned" / "churches_florida_cleaned.csv",
        "excel": output / "cleaned" / "churches_florida.xlsx",
        "log": output / "logs" / "scrape_log.txt",
        "failed": output / "logs" / "failed_urls.csv",
        "source": output / "logs" / "source_summary.csv",
        "dup": output / "logs" / "duplicate_review.csv",
        "summary": output / "logs" / "run_summary.json",
    }


def _needs_playwright(html: str, domain: str) -> bool:
    js_heavy_domains = ["wixsite", "squarespace", "churchcenter", "subsplash"]
    script_count = html.lower().count("<script")
    if len(html) < 2500 or script_count > 50:
        return True
    if any(d in domain for d in js_heavy_domains):
        return True
    return False


def _discover_urls(storage: Storage, logger, fetcher: PageFetcher, max_pages: int) -> int:
    search_provider = DuckDuckGoHtmlProvider(fetcher)
    engine = DiscoveryEngine(search_provider)

    total = 0
    for county in tqdm(FLORIDA_COUNTIES, desc="Discovering by county"):
        cities = get_cities_for_county(county)
        logger.info("Discovering county=%s cities=%d", county, len(cities))
        discovered = engine.discover(county, cities)
        for item in discovered:
            storage.upsert_discovered_url(item.url, item.county, item.city, item.source_type)
            total += 1
            if total >= max_pages:
                return total
    return total


def _scrape_pending(
    storage: Storage,
    logger,
    fetcher: PageFetcher,
    use_playwright: bool,
    max_pages: int,
) -> tuple[list[RawChurchRecord], list[SourceResult], list[dict]]:
    raw_records: list[RawChurchRecord] = []
    source_results: list[SourceResult] = []
    failed_urls: list[dict] = []

    pw = PlaywrightFetcher() if use_playwright else None
    pending = storage.pending_urls(max_pages)

    for row in tqdm(pending, desc="Scraping URLs"):
        url = row["url"]
        county = row["county"]

        res = fetcher.fetch(url)
        parser_used = "requests"
        html = res.text

        if use_playwright and pw and (res.error or _needs_playwright(html, row["source_type"] or "")):
            pw_res = pw.fetch(url)
            if pw_res.html:
                html = pw_res.html
                parser_used = "playwright"
            elif res.error:
                failed_urls.append({"url": url, "error": res.error, "county": county})
                storage.mark_url_status(url, "failed")
                storage.save_fetched_page(url, res.status_code, False, parser_used, res.error)
                source_results.append(
                    SourceResult(
                        source_url=url,
                        source_domain=(row["source_type"] or "unknown"),
                        county=county,
                        fetched_ok=False,
                        status_code=res.status_code,
                        parser_used=parser_used,
                        error=res.error,
                    )
                )
                continue

        if res.error and not html:
            logger.warning("Failed fetch: %s | %s", url, res.error)
            failed_urls.append({"url": url, "error": res.error, "county": county})
            storage.mark_url_status(url, "failed")
            storage.save_fetched_page(url, res.status_code, False, parser_used, res.error)
            source_results.append(
                SourceResult(
                    source_url=url,
                    source_domain=(row["source_type"] or "unknown"),
                    county=county,
                    fetched_ok=False,
                    status_code=res.status_code,
                    parser_used=parser_used,
                    error=res.error,
                )
            )
            continue

        try:
            record = extract_church_record(html=html, source_url=url, county=county)
            if record.church_name:
                raw_records.append(record)

            # expand extraction via likely subpages
            soup = parse_html(html)
            for sub_url in relevant_subpage_links(soup, url)[:4]:
                sub_res = fetcher.fetch(sub_url)
                if not sub_res.text:
                    continue
                sub_rec = extract_church_record(sub_res.text, sub_url, county)
                if sub_rec.church_name:
                    raw_records.append(sub_rec)

            storage.mark_url_status(url, "done")
            storage.save_fetched_page(url, res.status_code, True, parser_used, None)
            source_results.append(
                SourceResult(
                    source_url=url,
                    source_domain=(row["source_type"] or "unknown"),
                    county=county,
                    fetched_ok=True,
                    status_code=res.status_code,
                    parser_used=parser_used,
                    records_extracted=1,
                )
            )
        except Exception as exc:
            err = str(exc)
            logger.exception("Parse error on %s", url)
            failed_urls.append({"url": url, "error": err, "county": county})
            storage.mark_url_status(url, "failed")
            storage.save_fetched_page(url, res.status_code, False, parser_used, err)

    return raw_records, source_results, failed_urls


@app.command()
def run(
    state: str = typer.Option("Florida", help="Target state."),
    max_pages: int = typer.Option(settings.max_pages, help="Maximum pages to discover/scrape."),
    use_playwright: bool = typer.Option(settings.use_playwright, help="Enable Playwright fallback."),
    export: list[str] = typer.Option(["csv", "excel"], help="Export formats: csv excel"),
) -> None:
    """Execute full discover -> scrape -> normalize -> dedupe -> export pipeline."""
    if state.lower() != "florida":
        typer.echo("This build is currently configured for Florida only.")
        raise typer.Exit(code=1)

    paths = _paths()
    logger = get_logger(paths["log"])
    storage = Storage(settings.sqlite_db_path)
    fetcher = PageFetcher()

    run_started = datetime.utcnow()
    logger.info("Run started for state=%s", state)
    discovered_count = _discover_urls(storage, logger, fetcher, max_pages=max_pages)

    raw_records, source_results, failed_urls = _scrape_pending(
        storage=storage,
        logger=logger,
        fetcher=fetcher,
        use_playwright=use_playwright,
        max_pages=max_pages,
    )

    storage.save_records("raw_records", [r.model_dump(mode="json") for r in raw_records])

    clean_records: list[CleanChurchRecord] = []
    for raw in raw_records:
        clean = normalize_record(raw)
        if not clean:
            continue
        if settings.enable_geocoding and clean.street_address and clean.city and not (clean.latitude and clean.longitude):
            full_addr = f"{clean.street_address}, {clean.city}, FL {clean.zip_code or ''}".strip()
            lat, lon = geocode_address(full_addr)
            clean.latitude, clean.longitude = lat, lon
        clean_records.append(clean)

    deduped, duplicate_flags = deduplicate_records(clean_records, fuzzy_threshold=settings.fuzzy_dup_threshold)
    storage.save_records("clean_records", [r.model_dump(mode="json") for r in deduped])

    export_raw_csv(raw_records, paths["raw_csv"])
    export_clean_csv(deduped, paths["clean_csv"])
    export_logs(failed_urls, source_results, duplicate_flags, paths["failed"], paths["source"], paths["dup"])

    if "excel" in [x.lower() for x in export]:
        export_excel(deduped, source_results, failed_urls, paths["excel"])

    run_summary = ScrapeRunSummary(
        run_started_at=run_started,
        run_finished_at=datetime.utcnow(),
        total_discovered_urls=discovered_count,
        total_fetched_urls=len(source_results),
        total_failed_urls=len(failed_urls),
        total_raw_records=len(raw_records),
        total_clean_records=len(deduped),
        duplicates_flagged=len(duplicate_flags),
        counties_processed=len(FLORIDA_COUNTIES),
        notes=["Use selectors tuning for directories/search markup changes as needed."],
    )

    paths["summary"].parent.mkdir(parents=True, exist_ok=True)
    paths["summary"].write_text(run_summary.model_dump_json(indent=2), encoding="utf-8")

    logger.info("Run complete raw=%d clean=%d failures=%d", len(raw_records), len(deduped), len(failed_urls))
    typer.echo("Run completed. See data/ and logs/ output folders.")


@app.command()
def resume() -> None:
    """Resume by scraping still-pending URLs from SQLite queue."""
    run(
        state="Florida",
        max_pages=settings.max_pages,
        use_playwright=settings.use_playwright,
        export=["csv", "excel"],
    )


@app.command()
def summary() -> None:
    """Display high-level summary from latest run artifacts."""
    paths = _paths()
    if not paths["summary"].exists():
        typer.echo("No run summary found yet.")
        raise typer.Exit(code=0)

    data = json.loads(paths["summary"].read_text(encoding="utf-8"))
    typer.echo(json.dumps(data, indent=2))


@app.command()
def counties() -> None:
    """List all configured Florida counties and starter cities."""
    for county in FLORIDA_COUNTIES:
        typer.echo(f"{county}: {', '.join(COUNTY_TO_CITIES.get(county, []))}")


if __name__ == "__main__":
    app()
