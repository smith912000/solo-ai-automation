"""
Basic enrichment utilities.
Only called by worker.
"""

from __future__ import annotations

import re
import os
import socket
import time
import urllib.request
from html import unescape
from typing import Optional


_INDUSTRY_KEYWORDS = [
    ("fintech", "Financial Services"),
    ("bank", "Financial Services"),
    ("payment", "Financial Services"),
    ("health", "Healthcare"),
    ("medical", "Healthcare"),
    ("clinic", "Healthcare"),
    ("ecommerce", "Ecommerce"),
    ("e-commerce", "Ecommerce"),
    ("retail", "Retail"),
    ("saas", "Software"),
    ("software", "Software"),
    ("ai", "Software"),
    ("agency", "Agency"),
    ("marketing", "Marketing"),
    ("construction", "Construction"),
    ("logistics", "Logistics"),
    ("manufacturing", "Manufacturing"),
]

_CACHE: dict[str, dict] = {}


def _normalize_domain(website: str) -> str:
    domain = re.sub(r"^https?://", "", website).split("/")[0]
    return domain.lower()


def _normalize_root_url(website: str) -> str:
    if not website.startswith(("http://", "https://")):
        website = f"https://{website}"
    domain = _normalize_domain(website)
    return f"https://{domain}"


def _get_cached(key: str) -> Optional[dict]:
    ttl_seconds = int(os.getenv("ENRICHMENT_CACHE_TTL_SECONDS", "3600"))
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["timestamp"] > ttl_seconds:
        _CACHE.pop(key, None)
        return None
    return entry["data"]


def _set_cached(key: str, data: dict) -> None:
    _CACHE[key] = {"timestamp": time.time(), "data": data}


def _extract_title(html: str) -> Optional[str]:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        return unescape(match.group(1)).strip()
    return None


def _extract_meta_description(html: str) -> Optional[str]:
    patterns = [
        r'<meta[^>]+name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]*content=["\'](.*?)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            return unescape(match.group(1)).strip()
    return None


def _extract_linkedin(html: str) -> dict:
    match = re.search(
        r"https?://(www\.)?linkedin\.com/company/([a-zA-Z0-9\-_/]+)",
        html,
        re.IGNORECASE,
    )
    if not match:
        return {"linkedin_company": None, "linkedin_url": None}
    slug = match.group(2).strip("/").split("/")[0]
    url = f"https://www.linkedin.com/company/{slug}"
    return {"linkedin_company": slug, "linkedin_url": url}


def _estimate_company_size(html: str) -> Optional[str]:
    match = re.search(r"(\d{1,6})\s*\+?\s*employees", html, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if count < 10:
            return "1-9"
        if count < 50:
            return "10-49"
        if count < 200:
            return "50-199"
        if count < 1000:
            return "200-999"
        return "1000+"
    return None


def _infer_industry(text: str) -> str:
    text = text.lower()
    for keyword, industry in _INDUSTRY_KEYWORDS:
        if keyword in text:
            return industry
    return "Unknown"


def _fetch_html(url: str) -> Optional[str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "solo-ai-automation/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status >= 400:
                return None
            return response.read(200_000).decode("utf-8", errors="ignore")
    except (OSError, ValueError, socket.timeout):
        return None


def _enrich_from_root_url(root_url: str) -> dict:
    html = _fetch_html(root_url)
    if not html:
        return {"source": "basic", "description": None, "industry": "Unknown", "size": "Unknown"}

    title = _extract_title(html)
    description = _extract_meta_description(html) or title
    size = _estimate_company_size(html) or "Unknown"
    industry = _infer_industry(f"{title or ''} {description or ''}")
    linkedin_data = _extract_linkedin(html)

    return {
        "source": "scrape",
        "title": title,
        "description": description,
        "industry": industry,
        "size": size,
        "company_size": size,
        **linkedin_data,
    }


def enrich_company(website: Optional[str]) -> dict:
    """Best-effort enrichment using website metadata."""
    if not website:
        return {}

    domain = _normalize_domain(website)
    root_url = _normalize_root_url(website)
    cached = _get_cached(root_url)
    if cached:
        return {"domain": domain, **cached}
    enrichment = _enrich_from_root_url(root_url)
    _set_cached(root_url, enrichment)
    return {"domain": domain, **enrichment}
