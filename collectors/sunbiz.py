from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from config import PipelineConfig


@dataclass
class SunbizRecord:
    entity_name: str
    document_number: str
    status: str
    entity_type: str
    filing_date: str
    principal_address: str
    mailing_address: str
    source_url: str


def _session(config: PipelineConfig) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": config.user_agent})
    return s


def _fetch(session: requests.Session, url: str, config: PipelineConfig) -> str:
    for attempt in range(1, config.retries + 1):
        try:
            resp = session.get(url, timeout=config.timeout_seconds)
            resp.raise_for_status()
            time.sleep(config.rate_limit_seconds)
            return resp.text
        except Exception:
            if attempt == config.retries:
                raise
            time.sleep(config.rate_limit_seconds * attempt)
    raise RuntimeError("unreachable")


def _parse_detail(html: str) -> tuple[str, str, str, str]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    def pick(prefix: str) -> str:
        for line in text.splitlines():
            if line.lower().startswith(prefix.lower()):
                return line.split(":", 1)[-1].strip()
        return ""

    return (
        pick("Status"),
        pick("FEI/EIN Number") or pick("Document Number"),
        pick("Principal Address"),
        pick("Mailing Address"),
    )


def collect_sunbiz(config: PipelineConfig, keywords: Iterable[str]) -> list[dict]:
    log = logging.getLogger(__name__)
    session = _session(config)
    rows: list[dict] = []

    for keyword in keywords:
        page = 1
        while True:
            search_url = (
                f"{config.sunbiz_base}/SearchResults/EntityName/{quote(keyword)}/Page{page}"
            )
            try:
                html = _fetch(session, search_url, config)
            except Exception as exc:
                log.warning("Sunbiz search failed for %s page %s: %s", keyword, page, exc)
                break

            soup = BeautifulSoup(html, "html.parser")
            links = [a for a in soup.select("a") if "/Inquiry/CorporationSearch/" in a.get("href", "")]
            detail_links = []
            for a in links:
                href = a.get("href", "")
                if "SearchResults" in href or "Page" in href:
                    continue
                if href.startswith("/"):
                    href = f"https://search.sunbiz.org{href}"
                if "Detail" in href or "CorporationSearchBy" in href:
                    detail_links.append((a.get_text(strip=True), href))
            if not detail_links:
                break

            for name, detail_url in detail_links:
                try:
                    detail_html = _fetch(session, detail_url, config)
                    status, doc, principal, mailing = _parse_detail(detail_html)
                except Exception as exc:
                    log.warning("Sunbiz detail failed %s: %s", detail_url, exc)
                    status, doc, principal, mailing = "", "", "", ""
                rows.append(
                    {
                        "keyword": keyword,
                        "entity_name": name,
                        "document_number": doc,
                        "status": status,
                        "entity_type": "",
                        "filing_date": "",
                        "principal_address": principal,
                        "mailing_address": mailing,
                        "source_url": detail_url,
                    }
                )

            page += 1
            if page > 25:
                break

    # deterministic order
    uniq = {}
    for r in rows:
        key = (r["entity_name"], r["document_number"], r["source_url"])
        uniq[key] = r
    return [uniq[k] for k in sorted(uniq)]
