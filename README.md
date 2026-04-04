# Florida Churches Data Pipeline (Python 3.11+)

This project builds an audit-friendly master spreadsheet of Florida churches by combining:

1. **Florida Sunbiz** entity-name search records (official Florida Division of Corporations search pages)
2. **IRS exempt organization** records (from bulk file input)
3. **OpenStreetMap (Overpass)** mapped church locations

## Project structure

- `main.py`
- `config.py`
- `requirements.txt`
- `collectors/sunbiz.py`
- `collectors/irs.py`
- `collectors/osm.py`
- `transform/normalize.py`
- `transform/match.py`
- `export/write_excel.py`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI usage

```bash
python main.py --run-all --output ./output
python main.py --sunbiz-only --output ./output
python main.py --irs-only --irs-bulk-file ./data/irs_eo_bmf.csv --output ./output
python main.py --osm-only --output ./output
```

## Output files

The pipeline writes the following files into the output folder:

1. `Florida_Churches_Master.xlsx`
2. `Florida_Churches_Master.csv`
3. `Florida_Churches_Sunbiz_Raw.csv`
4. `Florida_Churches_IRS_Raw.csv`
5. `Florida_Churches_OSM_Raw.csv`
6. `Florida_Churches_Duplicate_Review.xlsx`
7. `Florida_Churches_Unmatched_Review.xlsx`
8. `Florida_Churches_Run_Log.txt`

## Source contributions and limitations

### Sunbiz
- Contributes Florida entity registration context and status.
- Uses official name-search pages from the Division of Corporations.
- Limitation: HTML layout can change; principal/mailing/type/date completeness varies.

### IRS
- Contributes tax-exempt organization metadata such as EIN, subsection, foundation, ruling date, and revocation signal.
- Designed for IRS bulk files when available locally.
- Limitation: if no bulk file is provided, IRS raw output is empty by design.

### OSM
- Contributes physical mapped place-of-worship points and coordinates for spatial enrichment.
- Uses Overpass query for Florida `amenity=place_of_worship` + `religion=christian`.
- Limitation: crowd-sourced data can be incomplete or inconsistent.

## Matching logic

Records are matched via:
1. exact normalized name
2. fuzzy name similarity
3. city / ZIP comparison
4. coordinate proximity

A score from 0-100 is written to **Match Confidence Score** and low-confidence rows are flagged for review.

## Updating keyword lists

Update `SUNBIZ_KEYWORDS` in `config.py` and rerun the pipeline.

## Spreadsheet usage

Open `Florida_Churches_Master.xlsx` and use:
- **Master** for final reconciled records
- **Raw** tabs for source-level audit trail
- **Duplicate Review** and **Unmatched Review** tabs for manual QA
- **Data Dictionary** tab for field definitions

## ArcGIS Pro import guidance

1. For tabular import: use `Florida_Churches_Master.csv` in **Add Data**.
2. For map points: set X=`Longitude`, Y=`Latitude`, coordinate system WGS84 (EPSG:4326).
3. For preserving formatting/review tabs, use `Florida_Churches_Master.xlsx` as a workbook source.

## Reproducibility / governance

- Deterministic sorting before export
- Intermediate raw source CSV files preserved
- Run log persisted
- No fabrication of missing county/denomination/tax values
- Source provenance stored in `Raw Source URLs`
