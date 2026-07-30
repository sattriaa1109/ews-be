import logging
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
        results.append({
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", "").strip(),
            "source": parsed.feed.get("title", feed_url),
            "published_at": _parse_published(entry),
            "raw_summary": entry.get("summary", ""),
        })
    return results


def run_scrape_job():
    """Dipanggil oleh scheduler. Ambil semua feed, simpan artikel baru ke DB,
    lalu jalankan detector untuk tiap artikel baru."""
    from detector.detector import evaluate_article  # import lokal, hindari circular import

    db = SessionLocal()
    new_count = 0
    try:
        for feed_url in RSS_FEEDS:
            for item in fetch_feed(feed_url):
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

                evaluate_article(db, article)

        logger.info(f"Scrape job selesai. {new_count} artikel baru diproses.")
    finally:
        db.close()
