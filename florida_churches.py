#!/usr/bin/env python3
"""Generate an Excel spreadsheet of Florida churches using the Overpass API."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests
from openpyxl import Workbook

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SOURCE_NAME = "OpenStreetMap Overpass API"
FLORIDA_BBOX = (24.396308, -87.634938, 31.000968, -80.031362)

ADDRESS_KEYS = {
    "street": ("addr:street", "addr:housename"),
    "city": ("addr:city", "addr:town", "addr:village", "addr:hamlet"),
    "state": ("addr:state",),
    "zip": ("addr:postcode",),
    "county": ("addr:county", "is_in:county"),
}
DENOMINATION_KEYS = (
    "denomination",
    "religion:denomination",
    "church:denomination",
    "operator:type",
)


@dataclass
class ChurchRow:
    name: str
    denomination: str
    street: str
    city: str
    state: str
    zip: str
    county: str
    phone: str
    website: str
    email: str
    operator: str
    lat: float
    lon: float
    source: str
    source_url: str
    last_verified: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tile-size", type=float, default=0.5, help="Tile size in degrees (default: 0.5)")
    p.add_argument("--output", default="florida_churches.xlsx", help="Output Excel path")
    p.add_argument("--cache-dir", default=".cache/overpass", help="Directory for API cache")
    p.add_argument("--state-file", default=".cache/florida_progress.json", help="Resume/progress state file")
    p.add_argument("--resume", action="store_true", help="Resume from previous progress file")
    p.add_argument("--max-retries", type=int, default=5, help="Retry count per request")
    p.add_argument("--backoff-base", type=float, default=2.0, help="Exponential backoff base seconds")
    p.add_argument("--request-timeout", type=int, default=120, help="HTTP timeout seconds")
    p.add_argument("--sleep", type=float, default=1.0, help="Delay between tile requests seconds")
    p.add_argument("--max-tiles", type=int, default=None, help="Optional cap on processed tiles")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return p.parse_args()


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def normalize_state(value: str) -> str:
    val = normalize_whitespace(value).upper()
    if val in {"FL", "FLORIDA", ""}:
        return "FL"
    return val


def normalize_zip(value: str) -> str:
    val = normalize_whitespace(value)
    match = re.match(r"^(\d{5})(?:-\d{4})?$", val)
    return match.group(1) if match else val


def normalize_street(street: str, housenumber: str = "") -> str:
    st = normalize_whitespace(street)
    hn = normalize_whitespace(housenumber)
    if hn and st and not st.startswith(hn):
        st = f"{hn} {st}".strip()
    replacements = {
        r"\bStreet\b": "St",
        r"\bAvenue\b": "Ave",
        r"\bRoad\b": "Rd",
        r"\bBoulevard\b": "Blvd",
        r"\bDrive\b": "Dr",
        r"\bLane\b": "Ln",
        r"\bCourt\b": "Ct",
        r"\bHighway\b": "Hwy",
    }
    for pattern, repl in replacements.items():
        st = re.sub(pattern, repl, st, flags=re.IGNORECASE)
    return st


def normalize_name(name: str) -> str:
    return normalize_whitespace(name).title()


def chunk_bbox(min_lat: float, min_lon: float, max_lat: float, max_lon: float, tile_size: float) -> list[tuple[float, float, float, float]]:
    tiles: list[tuple[float, float, float, float]] = []
    lat = min_lat
    while lat < max_lat:
        next_lat = min(lat + tile_size, max_lat)
        lon = min_lon
        while lon < max_lon:
            next_lon = min(lon + tile_size, max_lon)
            tiles.append((lat, lon, next_lat, next_lon))
            lon = next_lon
        lat = next_lat
    return tiles


def tile_key(tile: tuple[float, float, float, float]) -> str:
    raw = ",".join(f"{n:.6f}" for n in tile)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def overpass_query(tile: tuple[float, float, float, float]) -> str:
    s, w, n, e = tile
    bbox = f"{s},{w},{n},{e}"
    return f"""
[out:json][timeout:90];
(
  node[\"amenity\"=\"place_of_worship\"][\"religion\"=\"christian\"]({bbox});
  node[\"building\"=\"church\"]({bbox});
  way[\"amenity\"=\"place_of_worship\"][\"religion\"=\"christian\"]({bbox});
  way[\"building\"=\"church\"]({bbox});
  relation[\"amenity\"=\"place_of_worship\"][\"religion\"=\"christian\"]({bbox});
  relation[\"building\"=\"church\"]({bbox});
);
out center tags;
""".strip()


def request_with_retry(session: requests.Session, query: str, timeout: int, max_retries: int, backoff_base: float) -> dict[str, Any]:
    for attempt in range(max_retries + 1):
        try:
            res = session.post(OVERPASS_URL, data=query.encode("utf-8"), timeout=timeout)
            if res.status_code == 429:
                raise requests.HTTPError("429 Too Many Requests", response=res)
            res.raise_for_status()
            return res.json()
        except (requests.RequestException, ValueError) as exc:
            if attempt >= max_retries:
                raise RuntimeError(f"Overpass request failed after {max_retries + 1} attempts") from exc
            sleep_for = backoff_base * math.pow(2, attempt)
            logging.warning("Request failed (attempt %s/%s): %s. Retrying in %.1fs", attempt + 1, max_retries + 1, exc, sleep_for)
            time.sleep(sleep_for)
    raise AssertionError("unreachable")


def get_cached_or_fetch(session: requests.Session, tile: tuple[float, float, float, float], cache_dir: Path, timeout: int, max_retries: int, backoff_base: float) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = tile_key(tile)
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    query = overpass_query(tile)
    data = request_with_retry(session, query, timeout, max_retries, backoff_base)
    cache_file.write_text(json.dumps(data), encoding="utf-8")
    return data


def get_tag(tags: dict[str, Any], keys: tuple[str, ...] | list[str]) -> str:
    for key in keys:
        val = tags.get(key)
        if val:
            return str(val)
    return ""


def church_from_element(el: dict[str, Any], verified_ts: str) -> ChurchRow | None:
    tags = el.get("tags") or {}
    name = normalize_name(tags.get("name", ""))
    denom = normalize_whitespace(get_tag(tags, DENOMINATION_KEYS))
    street = normalize_street(tags.get("addr:street", ""), tags.get("addr:housenumber", ""))
    city = normalize_whitespace(get_tag(tags, ADDRESS_KEYS["city"]))
    state = normalize_state(get_tag(tags, ADDRESS_KEYS["state"])) or "FL"
    zip_code = normalize_zip(get_tag(tags, ADDRESS_KEYS["zip"]))
    county = normalize_whitespace(get_tag(tags, ADDRESS_KEYS["county"]))
    phone = normalize_whitespace(tags.get("contact:phone", "") or tags.get("phone", ""))
    website = normalize_whitespace(tags.get("contact:website", "") or tags.get("website", ""))
    email = normalize_whitespace(tags.get("contact:email", "") or tags.get("email", ""))
    operator = normalize_whitespace(tags.get("operator", ""))

    lat = el.get("lat")
    lon = el.get("lon")
    center = el.get("center") or {}
    if lat is None:
        lat = center.get("lat")
    if lon is None:
        lon = center.get("lon")
    if lat is None or lon is None:
        return None

    source_url = f"https://www.openstreetmap.org/{el.get('type', 'node')}/{el.get('id')}"
    return ChurchRow(
        name=name,
        denomination=denom,
        street=street,
        city=city,
        state=state,
        zip=zip_code,
        county=county,
        phone=phone,
        website=website,
        email=email,
        operator=operator,
        lat=float(lat),
        lon=float(lon),
        source=SOURCE_NAME,
        source_url=source_url,
        last_verified=verified_ts,
    )


def exact_key(row: ChurchRow) -> tuple[str, str, str, str, str, str]:
    return (
        row.name.lower(),
        row.street.lower(),
        row.city.lower(),
        row.state.lower(),
        row.zip.lower(),
        f"{row.lat:.5f},{row.lon:.5f}",
    )


def fuzzy_key(row: ChurchRow) -> str:
    return "|".join([row.name.lower(), row.street.lower(), row.city.lower(), row.zip.lower()])


def is_fuzzy_duplicate(row: ChurchRow, existing: list[ChurchRow], threshold: float = 0.93) -> bool:
    key = fuzzy_key(row)
    for other in existing:
        if abs(row.lat - other.lat) > 0.002 or abs(row.lon - other.lon) > 0.002:
            continue
        score = SequenceMatcher(None, key, fuzzy_key(other)).ratio()
        if score >= threshold:
            return True
    return False


def row_missing_fields(row: ChurchRow) -> list[str]:
    missing = []
    if not row.name:
        missing.append("name")
    if not row.street:
        missing.append("street")
    if not row.city:
        missing.append("city")
    if not row.zip:
        missing.append("zip")
    if not row.county:
        missing.append("county")
    return missing


def write_excel(output: Path, rows: list[ChurchRow], exceptions: list[tuple[ChurchRow, str]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Churches"
    headers = [
        "name",
        "denomination",
        "street",
        "city",
        "state",
        "zip",
        "county",
        "phone",
        "website",
        "email",
        "operator",
        "lat",
        "lon",
        "source",
        "source_url",
        "last_verified",
    ]
    ws.append(headers)
    for r in rows:
        ws.append([
            r.name,
            r.denomination,
            r.street,
            r.city,
            r.state,
            r.zip,
            r.county,
            r.phone,
            r.website,
            r.email,
            r.operator,
            r.lat,
            r.lon,
            r.source,
            r.source_url,
            r.last_verified,
        ])

    ex = wb.create_sheet("Exceptions")
    ex.append(headers + ["missing_fields"])
    for r, reason in exceptions:
        ex.append([
            r.name,
            r.denomination,
            r.street,
            r.city,
            r.state,
            r.zip,
            r.county,
            r.phone,
            r.website,
            r.email,
            r.operator,
            r.lat,
            r.lon,
            r.source,
            r.source_url,
            r.last_verified,
            reason,
        ])
    wb.save(output)


def write_json(output: Path, rows: list[ChurchRow]) -> None:
    output.write_text(json.dumps([asdict(row) for row in rows], indent=2), encoding="utf-8")


@dataclass
class FloridaChurchesAgent:
    """Agent workflow for collecting Florida church records from Overpass."""

    args: argparse.Namespace

    def run(self) -> tuple[list[ChurchRow], list[tuple[ChurchRow, str]]]:
        tiles = chunk_bbox(*FLORIDA_BBOX, self.args.tile_size)
        if self.args.max_tiles:
            tiles = tiles[: self.args.max_tiles]
        state_file = Path(self.args.state_file)
        state = load_state(state_file) if self.args.resume else {"completed": []}
        completed = set(state.get("completed", []))

        rows: list[ChurchRow] = []
        exceptions: list[tuple[ChurchRow, str]] = []
        exact_seen: set[tuple[str, str, str, str, str, str]] = set()

        session = requests.Session()
        cache_dir = Path(self.args.cache_dir)
        verified_ts = datetime.now(timezone.utc).isoformat()

        for idx, tile in enumerate(tiles, start=1):
            key = tile_key(tile)
            if key in completed:
                logging.info("[%s/%s] Skipping completed tile %s", idx, len(tiles), key)
                continue
            logging.info("[%s/%s] Processing tile %s", idx, len(tiles), key)
            data = get_cached_or_fetch(
                session,
                tile,
                cache_dir=cache_dir,
                timeout=self.args.request_timeout,
                max_retries=self.args.max_retries,
                backoff_base=self.args.backoff_base,
            )
            for element in data.get("elements", []):
                row = church_from_element(element, verified_ts)
                if not row:
                    continue
                ek = exact_key(row)
                if ek in exact_seen:
                    continue
                if is_fuzzy_duplicate(row, rows):
                    continue
                exact_seen.add(ek)
                rows.append(row)
                missing = row_missing_fields(row)
                if missing:
                    exceptions.append((row, ",".join(missing)))

            completed.add(key)
            state["completed"] = sorted(completed)
            save_state(state_file, state)
            time.sleep(self.args.sleep)

        return rows, exceptions


def load_state(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"completed": []}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")
    agent = FloridaChurchesAgent(args)
    rows, exceptions = agent.run()

    write_excel(Path(args.output), rows, exceptions)
    write_json(Path(args.output).with_suffix(".json"), rows)
    logging.info("Wrote %s rows (%s exceptions) to %s", len(rows), len(exceptions), args.output)


if __name__ == "__main__":
    main()
