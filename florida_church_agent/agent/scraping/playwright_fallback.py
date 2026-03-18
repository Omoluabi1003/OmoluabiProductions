"""Optional Playwright fallback for dynamic pages."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def fetch_with_playwright(url: str, timeout_ms: int = 30000) -> str | None:
    try:
        from playwright.async_api import async_playwright
    except Exception:
        logger.warning("Playwright not installed; fallback unavailable")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=timeout_ms)
            content = await page.content()
            return content
        except Exception as exc:
            logger.warning("Playwright failed %s: %s", url, exc)
            return None
        finally:
            await browser.close()
