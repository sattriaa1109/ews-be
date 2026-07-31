import logging
import re
from datetime import datetime

import feedparser

from config import RSS_FEEDS
from database import SessionLocal
from models.tables import Article

logger = logging.getLogger("scraper")


def _parse_published(entry) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6])
    return None


def fetch_feed(feed_url: str) -> list[dict]:
    """Ambil semua entry dari satu RSS feed, return list of dict siap disimpan."""
    parsed = feedparser.parse(feed_url)
    if parsed.bozo:
        logger.warning(f"Feed bermasalah saat parsing: {feed_url}")

    results = []
    for entry in parsed.entries:
        # Prefer full content over summary for richer keyword detection
        raw = entry.get("summary", "") or ""
        if hasattr(entry, "content") and entry.content:
            raw = entry.content[0].get("value", raw)
        raw = re.sub(r"<[^>]+>", " ", raw)
        results.append({
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", "").strip(),
            "source": parsed.feed.get("title", feed_url),
            "published_at": _parse_published(entry),
            "raw_summary": raw,
        })
    return results


def run_scrape_job():
    """Dipanggil oleh scheduler. Ambil semua feed, simpan artikel baru ke DB,
    lalu jalankan detector untuk tiap artikel baru."""
    from detector.detector import evaluate_article  # import lokal, hindari circular import

    if not RSS_FEEDS:
        logger.warning("RSS_FEEDS kosong, tidak ada feed yang di-scrape")
        return

    db = SessionLocal()
    new_count = 0
    try:
        for feed_url in RSS_FEEDS:
            try:
                items = fetch_feed(feed_url)
            except Exception:
                logger.exception(f"Feed gagal diakses: {feed_url}")
                continue
            for item in items:
                if not item["link"]:
                    continue
                exists = db.query(Article).filter(Article.link == item["link"]).first()
                if exists:
                    continue

                article = Article(**item)
                db.add(article)
                db.commit()
                db.refresh(article)
                new_count += 1

                try:
                    evaluate_article(db, article)
                except Exception:
                    db.rollback()
                    logger.exception(f"Gagal memproses artikel: {item.get('title', 'unknown')}")

        logger.info(f"Scrape job selesai. {new_count} artikel baru diproses.")
    finally:
        db.close()
