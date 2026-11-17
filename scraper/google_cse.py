# scraper/google_cse.py — Mengambil berita dari Google Custom Search Engine (Programmable Search) API
import logging
from datetime import datetime

import requests

from config import (
    GOOGLE_CSE_API_KEY,
    GOOGLE_CSE_ID,
    GOOGLE_CSE_NUM_RESULTS,
    GOOGLE_CSE_QUERIES,
)
from scraper.scraper import detect_region

logger = logging.getLogger("google_cse")

CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def _parse_published_from_item(item: dict) -> datetime | None:
    """Coba ambil waktu terbit dari metadata pagemap CSE (jika tersedia)."""
    pagemap = item.get("pagemap") or {}
    metatags = pagemap.get("metatags") or []
    if not metatags:
        return None
    meta = metatags[0] or {}
    for key in (
        "article:published_time",
        "og:pubdate",
        "pubdate",
        "date",
        "dc.date",
        "dc.date.issued",
    ):
        value = meta.get(key)
        if not value:
            continue
        try:
            # Normalisasi format ISO 8601 sederhana (mis. akhiran Z)
            iso = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso)
            return dt.replace(tzinfo=None)
        except Exception:
            continue
    return None


def fetch_google_cse(query: str, num: int | None = None) -> list[dict]:
    """Ambil hasil pencarian dari Google CSE API untuk satu query.
    Mengembalikan list of dict dengan bentuk yang sama seperti fetch_feed().
    """
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        logger.warning("Google CSE belum dikonfigurasi (API key / CSE ID kosong)")
        return []

    params = {
        "key": GOOGLE_CSE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": min(max(num or GOOGLE_CSE_NUM_RESULTS, 1), 10),
        "lr": "lang_id",  # Prioritaskan hasil bahasa Indonesia
        "gl": "id",
    }

    try:
        response = requests.get(CSE_ENDPOINT, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception:
        logger.exception(f"Gagal mengambil hasil Google CSE untuk query: {query}")
        return []

    if "error" in data:
        logger.error(f"Google CSE API error untuk query '{query}': {data.get('error')}")
        return []

    results = []
    for item in data.get("items", []) or []:
        title = (item.get("title") or "").strip()
        link = (item.get("link") or "").strip()
        snippet = (item.get("snippet") or "").strip()
        source_name = (item.get("displayLink") or "Google CSE").strip()

        if not link:
            continue

        region = detect_region(link, source_name, title, snippet)
        results.append(
            {
                "title": title,
                "link": link,
                "source": source_name,
                "published_at": _parse_published_from_item(item),
                "raw_summary": snippet,
                "region": region,
            }
        )
    return results


def fetch_all_google_cse() -> list[dict]:
    """Ambil hasil Google CSE untuk semua query yang dikonfigurasi (deduplikasi per link)."""
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        return []

    seen_links: set[str] = set()
    all_items: list[dict] = []
    for query in GOOGLE_CSE_QUERIES:
        items = fetch_google_cse(query)
        for item in items:
            link = item.get("link")
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            all_items.append(item)
    logger.info(f"Google CSE menghasilkan {len(all_items)} item unik dari {len(GOOGLE_CSE_QUERIES)} query.")
    return all_items
