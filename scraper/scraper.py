# scraper/scraper.py — Mengambil berita dari RSS feed lalu menyimpannya ke database
import logging  # Untuk menulis log ke konsol
import re  # Regex, dipakai untuk membersihkan tag HTML dari teks artikel
from concurrent.futures import ThreadPoolExecutor, as_completed  # Unduh beberapa feed sekaligus
from datetime import datetime  # Membuat objek datetime dari hasil parsing feed

import requests  # Library HTTP untuk request dengan custom user-agent
import feedparser  # Library untuk membaca/mengurai feed RSS/Atom

from config import RSS_FEEDS, SCRAPER_MAX_WORKERS  # Daftar feed & jumlah worker (dari config)
from database import SessionLocal  # Pabrik sesi database
from models.tables import Article  # Model tabel artikel

logger = logging.getLogger("scraper")  # Logger khusus untuk modul scraper


def _parse_published(entry) -> datetime | None:
    """Mengubah waktu terbit dari feed (tuple) jadi objek datetime. None jika tidak ada."""
    if getattr(entry, "published_parsed", None):  # Cek apakah feed menyediakan info waktu terbit
        return datetime(*entry.published_parsed[:6])  # 6 nilai pertama tuple (tahun..detik) dijadikan datetime
    return None  # Tidak ada info waktu → kembalikan None


def detect_region(feed_url: str, source: str, title: str, summary: str) -> str:
    """Deteksi wilayah/regional berdasarkan feed URL, sumber, judul, dan ringkasan berita."""
    text = f"{feed_url} {source} {title} {summary}".lower()
    
    if any(k in text for k in ["sumut", "sumbar", "riau", "kepri", "lampung", "sumsel", "sumatera", "sumatra", "medan", "padang", "pekanbaru", "palembang", "bengkulu", "jambi", "aceh", "babel", "kepulauan riau", "batam", "tanjung pinang"]):
        return "Sumatra"
    elif any(k in text for k in ["jawa", "jakarta", "bandung", "surabaya", "semarang", "yogyakarta", "banten", "jabar", "jateng", "jatim"]):
        return "Jawa"
    elif any(k in text for k in ["kalimantan", "kaltim", "kalsel", "kalbar", "kalteng", "kalut", "samarinda", "banjarmasin", "pontianak", "balikpapan", "palangkaraya"]):
        return "Kalimantan"
    elif any(k in text for k in ["sulawesi", "makassar", "manado", "palu", "kendari", "gorontalo", "sulsel", "sulteng", "sultra"]):
        return "Sulawesi"
    elif any(k in text for k in ["papua", "jayapura", "merauke", "sorong", "timika", "irian"]):
        return "Papua"
    elif any(k in text for k in ["bali", "nusa tenggara", "ntb", "ntt", "kupang", "mataram", "denpasar"]):
        return "Bali & Nusa Tenggara"
    elif any(k in text for k in ["maluku", "ambon", "ternate"]):
        return "Maluku"
    
    return "Nasional"


def fetch_feed(feed_url: str) -> list[dict]:
    """Ambil semua entry dari satu RSS feed menggunakan mobile user-agent, return list of dict siap disimpan."""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    response = requests.get(feed_url, headers=headers, timeout=15)
    response.raise_for_status()
    parsed = feedparser.parse(response.text)  # Unduh & urai feed dari URL
    if parsed.bozo:  # bozo = penanda bahwa feed tidak valid/bermasalah
        logger.warning(f"Feed bermasalah saat parsing: {feed_url}")  # Log peringatan tapi tetap lanjut

    results = []  # Wadah untuk hasil akhir
    for entry in parsed.entries:  # Loop tiap item/berita di dalam feed
        # Prefer full content over summary for richer keyword detection
        raw = entry.get("summary", "") or ""  # Ambil ringkasan feed (default string kosong)
        if hasattr(entry, "content") and entry.content:  # Kalau tersedia konten penuh
            raw = entry.content[0].get("value", raw)  # Gunakan konten penuh (lebih kaya kata kunci)
        raw = re.sub(r"<[^>]+>", " ", raw)  # Buang semua tag HTML, diganti spasi
        
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        source_name = parsed.feed.get("title", feed_url) or feed_url

        # Google News menyertakan nama media asli di elemen <source>.
        # Pakai nama itu supaya sumber yang tersimpan lebih informatif.
        entry_source = entry.get("source")
        if isinstance(entry_source, dict) and entry_source.get("title"):
            media_name = entry_source["title"]
            # Judul Google News berformat "Judul Berita - Nama Media"; buang suffix-nya.
            suffix = f" - {media_name}"
            if title.endswith(suffix):
                title = title[: -len(suffix)].strip()
            source_name = media_name

        region = detect_region(feed_url, source_name, title, raw)
        
        results.append({  # Simpan artikel sebagai dict
            "title": title,  # Judul artikel, spasi pinggir dibersihkan
            "link": link,  # URL artikel, spasi pinggir dibersihkan
            "source": source_name,  # Nama sumber (nama feed, fallback ke URL)
            "published_at": _parse_published(entry),  # Waktu terbit artikel (atau None)
            "raw_summary": raw,  # Teks polos isi artikel (tanpa HTML)
            "region": region,
        })
    return results  # Kembalikan daftar artikel


def _store_and_process_items(db, items, evaluate_article, send_alert_notification) -> int:
    """Simpan item artikel baru ke DB dan jalankan detector/notifier. Kembalikan jumlah artikel baru."""
    new_count = 0
    for item in items:
        if not item.get("link"):
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
            alert = evaluate_article(db, article)
            if alert:
                send_alert_notification(article, alert)
        except Exception:
            db.rollback()
            logger.exception(f"Gagal memproses artikel: {item.get('title', 'unknown')}")
    return new_count


def run_scrape_job():
    """Dipanggil oleh scheduler. Ambil semua feed (RSS + Google CSE bila dikonfigurasi),
    simpan artikel baru ke DB, lalu jalankan detector untuk tiap artikel baru."""
    from detector.detector import evaluate_article  # import lokal, hindari circular import
    from notifier.telegram_bot import send_alert_notification  # import lokal, hindari circular import
    from config import GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID

    if not RSS_FEEDS and not (GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID):
        logger.warning("Tidak ada sumber berita yang dikonfigurasi (RSS_FEEDS & Google CSE kosong)")
        return

    db = SessionLocal()
    new_count = 0
    try:
        # 1) Unduh semua RSS feed secara paralel; penulisan ke DB tetap di thread utama.
        if RSS_FEEDS:
            max_workers = max(1, SCRAPER_MAX_WORKERS)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_feed, feed_url): feed_url for feed_url in RSS_FEEDS}
                for future in as_completed(futures):
                    feed_url = futures[future]
                    try:
                        items = future.result()
                    except Exception:
                        logger.exception(f"Feed gagal diakses: {feed_url}")
                        continue
                    new_count += _store_and_process_items(db, items, evaluate_article, send_alert_notification)

        # 2) Ambil hasil dari Google Custom Search Engine API (jika dikonfigurasi).
        if GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID:
            try:
                from scraper.google_cse import fetch_all_google_cse
                cse_items = fetch_all_google_cse()
                new_count += _store_and_process_items(db, cse_items, evaluate_article, send_alert_notification)
            except Exception:
                logger.exception("Gagal mengambil data dari Google CSE API")

        logger.info(f"Scrape job selesai. {new_count} artikel baru diproses.")
    finally:
        db.close()
