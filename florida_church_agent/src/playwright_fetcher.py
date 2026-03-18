"""Playwright fallback fetcher for JS-heavy pages."""

from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import sync_playwright


@dataclass
class PlaywrightFetchResult:
    url: str
    html: str
    error: str | None = None


class PlaywrightFetcher:
    """Simple synchronous Playwright renderer."""

    def fetch(self, url: str, timeout_ms: int = 25000) -> PlaywrightFetchResult:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                html = page.content()
                browser.close()
            return PlaywrightFetchResult(url=url, html=html)
        except Exception as exc:
            return PlaywrightFetchResult(url=url, html="", error=str(exc))
