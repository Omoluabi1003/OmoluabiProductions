from __future__ import annotations

import logging
import time

import requests

from config import PipelineConfig


OVERPASS_QUERY = """
[out:json][timeout:300];
area["ISO3166-2"="US-FL"][admin_level=4]->.searchArea;
(
  node["amenity"="place_of_worship"]["religion"="christian"](area.searchArea);
  way["amenity"="place_of_worship"]["religion"="christian"](area.searchArea);
  relation["amenity"="place_of_worship"]["religion"="christian"](area.searchArea);
);
out center tags;
""".strip()


def collect_osm(config: PipelineConfig) -> list[dict]:
    log = logging.getLogger(__name__)
    headers = {"User-Agent": config.user_agent}
    payload = {"data": OVERPASS_QUERY}

    for attempt in range(1, config.retries + 1):
        try:
            resp = requests.post(
                config.overpass_url,
                data=payload,
                headers=headers,
                timeout=config.timeout_seconds * 2,
            )
            resp.raise_for_status()
            data = resp.json()
            rows = []
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                lat = el.get("lat") or (el.get("center") or {}).get("lat")
                lon = el.get("lon") or (el.get("center") or {}).get("lon")
                osm_type = el.get("type", "")
                osm_id = el.get("id", "")
                rows.append(
                    {
                        "osm_id": f"{osm_type}/{osm_id}",
                        "name": tags.get("name", ""),
                        "denomination": tags.get("denomination", ""),
                        "religion": tags.get("religion", ""),
                        "street": " ".join(x for x in [tags.get("addr:housenumber", ""), tags.get("addr:street", "")] if x).strip(),
                        "city": tags.get("addr:city", ""),
                        "state": tags.get("addr:state", ""),
                        "postcode": tags.get("addr:postcode", ""),
                        "latitude": lat,
                        "longitude": lon,
                        "source_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
                    }
                )
            rows.sort(key=lambda r: (r["name"], r["osm_id"]))
            return rows
        except Exception as exc:
            if attempt == config.retries:
                log.warning("OSM collection failed: %s", exc)
                return []
            time.sleep(config.rate_limit_seconds * attempt)
    return []
