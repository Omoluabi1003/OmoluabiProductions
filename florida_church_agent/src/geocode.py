"""Optional geocoding support via pluggable providers."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus

import requests

from config import settings


def geocode_address(address: str) -> tuple[Optional[float], Optional[float]]:
    """Geocode an address based on configured provider."""
    provider = settings.geocode_provider.lower()
    if provider == "nominatim":
        return _geocode_nominatim(address)
    if provider == "google":
        return _geocode_google(address)
    if provider == "mapbox":
        return _geocode_mapbox(address)
    if provider == "positionstack":
        return _geocode_positionstack(address)
    return None, None


def _geocode_nominatim(address: str) -> tuple[Optional[float], Optional[float]]:
    url = f"https://nominatim.openstreetmap.org/search?q={quote_plus(address)}&format=json&limit=1"
    resp = requests.get(url, timeout=settings.request_timeout, headers={"User-Agent": "florida-church-agent/1.0"})
    data = resp.json() if resp.ok else []
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None


def _geocode_google(address: str) -> tuple[Optional[float], Optional[float]]:
    if not settings.google_geocoding_api_key:
        return None, None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    resp = requests.get(
        url,
        params={"address": address, "key": settings.google_geocoding_api_key},
        timeout=settings.request_timeout,
    )
    data = resp.json() if resp.ok else {}
    results = data.get("results", [])
    if results:
        loc = results[0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    return None, None


def _geocode_mapbox(address: str) -> tuple[Optional[float], Optional[float]]:
    if not settings.mapbox_api_key:
        return None, None
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote_plus(address)}.json"
    resp = requests.get(
        url,
        params={"access_token": settings.mapbox_api_key, "limit": 1},
        timeout=settings.request_timeout,
    )
    data = resp.json() if resp.ok else {}
    feats = data.get("features", [])
    if feats:
        lon, lat = feats[0]["center"]
        return float(lat), float(lon)
    return None, None


def _geocode_positionstack(address: str) -> tuple[Optional[float], Optional[float]]:
    if not settings.positionstack_api_key:
        return None, None
    url = "http://api.positionstack.com/v1/forward"
    resp = requests.get(
        url,
        params={"access_key": settings.positionstack_api_key, "query": address, "limit": 1},
        timeout=settings.request_timeout,
    )
    data = resp.json() if resp.ok else {}
    items = data.get("data", [])
    if items:
        return items[0].get("latitude"), items[0].get("longitude")
    return None, None
