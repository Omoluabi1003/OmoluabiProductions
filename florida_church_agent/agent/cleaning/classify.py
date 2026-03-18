"""Source type classification logic."""

from __future__ import annotations

from urllib.parse import urlparse

DIRECTORY_HOSTS = {"yelp.com", "yellowpages.com", "faithstreet.com"}
DENOM_HOSTS = {"sbc.net", "umc.org", "catholic.org"}


def classify_source(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    if any(h in host for h in DIRECTORY_HOSTS):
        return "directory_listing"
    if any(h in host for h in DENOM_HOSTS):
        return "denominational_locator"
    if host.endswith(".org") or "church" in host:
        return "official_church_website"
    return "miscellaneous"
