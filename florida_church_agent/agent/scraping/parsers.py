"""HTML parsers to extract core church fields."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


def extract_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    keywords = ("contact", "about", "staff", "visit", "service")
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = a.get_text(" ", strip=True).lower()
        if any(k in href.lower() or k in text for k in keywords):
            links.append(href)
    return list(dict.fromkeys(links))


def extract_contact_fields(html: str) -> dict[str, str]:
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    return {
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
    }


def extract_social_links(base_url: str, html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    socials = {"facebook": "", "instagram": "", "youtube": ""}
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        host = urlparse(href).netloc.lower()
        if "facebook.com" in host and not socials["facebook"]:
            socials["facebook"] = href
        if "instagram.com" in host and not socials["instagram"]:
            socials["instagram"] = href
        if "youtube.com" in host or "youtu.be" in host:
            if not socials["youtube"]:
                socials["youtube"] = href
    return socials
