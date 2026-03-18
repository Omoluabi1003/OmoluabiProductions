# Florida Church Agent

A production-grade Python discovery + scraping pipeline for building a structured church database across all 67 counties in Florida.

## What this tool does

The agent discovers, scrapes, normalizes, deduplicates, and exports church records from publicly accessible web pages. It is designed for ethical, maintainable automation and source-level auditability.

## Features

- County-by-county + city-level search expansion for all Florida counties
- Layered discovery queries by denomination and location
- Modular search provider abstraction (default: DuckDuckGo HTML provider)
- Domain classification (official church, directory, denominational locator, miscellaneous)
- Static fetching (`requests`) with retries, user-agent rotation, and rate limiting
- Optional JavaScript fallback with Playwright
- Multi-page extraction heuristics (home/contact/about/staff/visit/service pages)
- Pydantic data models for raw and clean records
- Normalization of state, phones, emails, denomination vocabulary, canonical websites
- Layered deduplication (exact + fuzzy with RapidFuzz)
- Optional geocoding providers (Nominatim, Google, Mapbox, Positionstack)
- SQLite checkpointing and resume support
- CSV + Excel outputs with run logs and source/duplicate audit artifacts

## Installation

```bash
cd florida_church_agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Playwright setup

If you use Playwright fallback:

```bash
playwright install chromium
```

## How to run

```bash
python main.py run --state Florida
python main.py run --state Florida --max-pages 5000
python main.py run --state Florida --use-playwright
python main.py run --state Florida --export csv --export excel
python main.py resume
python main.py summary
python main.py counties
```

## Output files

Generated in `data/`:

- `data/raw/churches_florida_raw.csv`
- `data/cleaned/churches_florida_cleaned.csv`
- `data/cleaned/churches_florida.xlsx`
- `data/logs/scrape_log.txt`
- `data/logs/failed_urls.csv`
- `data/logs/source_summary.csv`
- `data/logs/duplicate_review.csv`
- `data/logs/run_summary.json`

## Legal and ethical scraping notes

- Scrapes only publicly accessible pages
- Does **not** bypass logins, CAPTCHAs, or access restrictions
- Uses polite delays and rotates user agents
- Checks `robots.txt` with best-effort handling before fetch
- Stores only organization-level contact data relevant to church listings

## Limitations

- Search engine markup can change, requiring selector tuning
- Some sites block bots or require JS rendering
- Address and pastor/service extraction are heuristic and not guaranteed
- Coverage depends on discoverability from public web sources

## Ideas for scaling

- Add additional search providers (SerpAPI/Bing API/custom index)
- Add distributed queue workers (Celery/RQ/Kafka)
- Add richer parser templates by CMS type (Wix, Squarespace, WordPress)
- Add county/city enrichment from Census gazetteers
- Add monitoring/metrics dashboards and quality scoring review UI
