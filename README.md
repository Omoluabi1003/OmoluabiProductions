# Ariyo-Style CLI Chatbot

A conversation-only chatbot with a warm, respectful tone and session memory.

## How to run

```bash
python main.py
```

## How to run tests

```bash
python -m unittest
```

## How to add a new intent and response rule

1. Add a new intent name and keyword rules in `bot/intents.py` inside `IntentDetector.intent_rules`.
2. Add a response template in `bot/persona.py` inside `AriyoPersona.responses`, or add special handling in
   `AriyoPersona.generate_response` if the intent needs dynamic content.
3. Add or update tests in `tests/test_intents.py` to cover the new intent.

---

## Florida Churches Excel Generator (Python 3.11)

This repository now includes `florida_churches.py`, an agent-style data pipeline that uses the **OpenStreetMap Overpass API** (no random site scraping) to collect Florida churches and build export files.

### Install dependencies

```bash
python3.11 -m pip install -r requirements-florida-churches.txt
```

### Run

```bash
python3.11 florida_churches.py --tile-size 0.5 --output florida_churches.xlsx
```

### Useful options

```bash
python3.11 florida_churches.py \
  --tile-size 0.4 \
  --cache-dir .cache/overpass \
  --state-file .cache/florida_progress.json \
  --resume \
  --max-retries 5 \
  --backoff-base 2 \
  --sleep 1.2
```

- `--tile-size`: controls Florida bounding-box tiling granularity (smaller tiles reduce API payload size).
- `--resume`: reuses the state file and skips already-completed tiles.
- Cache is stored as per-tile JSON responses in `--cache-dir`.

### Output fields

The script writes:
- an Excel workbook (`--output`, default `florida_churches.xlsx`)
- a JSON export with the same basename (for example, `florida_churches.json`)

The `Churches` sheet / JSON objects contain:

- `name`
- `denomination` (from denomination-like OSM tags when present)
- `street`
- `city`
- `state`
- `zip`
- `county` (derived from available OSM county tags when present)
- `phone`
- `website`
- `email`
- `operator`
- `lat`
- `lon`
- `source`
- `source_url`
- `last_verified`

Rows with incomplete key address fields are duplicated into an `Exceptions` sheet with a `missing_fields` reason.
### Data provenance and rate-limiting notes

- **Source**: OpenStreetMap data via Overpass endpoint `https://overpass-api.de/api/interpreter`.
- `source_url` points to the canonical OSM object URL for each record.
- Overpass is community infrastructure; use conservative request rates (`--sleep`) and retries with backoff.
- Cached tile responses reduce repeat load and improve reproducibility.
