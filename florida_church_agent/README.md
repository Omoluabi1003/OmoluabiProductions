# Florida Church Discovery Agent

Production-grade discovery and scraping pipeline for ETL GIS Consulting LLC focused on publicly accessible Florida church data across all 67 counties.

## Features
- Layered discovery queries by county and major city hints.
- DuckDuckGo HTML provider abstraction.
- Requests-based fetcher with retries, delays, robots.txt best effort checks.
- Optional Playwright fallback for JS-heavy pages.
- Record extraction, classification, normalization, and fuzzy dedupe.
- SQLite checkpointing for discovery/fetch/parse/export state.
- CSV, Excel, duplicate review, failed URL, and JSON run summary exports.
- CLI runtime independent of the optional local monitoring dashboard.
- PyInstaller packaging for Windows executables.

## Project structure
```text
florida_church_agent/
  agent/
    ...
  tests/
  data/
  main.py
  requirements.txt
  .env.example
  build_exe.bat
  church_agent.spec
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## Configure environment
Edit `.env` and set runtime values. Do not commit `.env`.

## Optional Playwright setup
```bash
python -m playwright install chromium
```

## Run
```bash
python main.py run --state Florida
python main.py run --state Florida --max-pages 5000
python main.py run --state Florida --use-playwright
python main.py run --state Florida --export csv --export excel
python main.py resume
python main.py summary
python main.py counties
python main.py serve-dashboard
```

## Outputs
- `data/raw/churches_florida_raw.csv`
- `data/cleaned/churches_florida_cleaned.csv`
- `data/cleaned/churches_florida.xlsx`
- `data/logs/failed_urls.csv`
- `data/logs/source_summary.csv`
- `data/logs/duplicate_review.csv`
- `data/logs/run_summary.json`
- `data/logs/scrape_log.txt`

## Build Windows executable
```bat
build_exe.bat
```
or:
```bash
pyinstaller --clean church_agent.spec
```

## Ethical scraping notes
- Use only publicly available pages.
- Respect robots and terms of service.
- Apply conservative delays in `SAFE_MODE`.
- Avoid collecting private or restricted data.

## Limitations
- Heuristic extraction can miss fields on non-standard templates.
- robots.txt checks are best-effort.
- Directory pages may contain stale information.
- Playwright adds heavy dependencies and runtime cost.

## Future improvements
- Add geocoding confidence and GIS-ready lat/lon columns.
- Add first-class ArcGIS/GeoPandas export profiles.
- Add richer denomination ontology and NER extraction.
- Add async queue orchestration for high-volume runs.
