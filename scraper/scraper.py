# scraper/scraper.py — Mengambil berita dari RSS feed lalu menyimpannya ke database
import logging  # Untuk menulis log ke konsol
import re  # Regex, dipakai untuk membersihkan tag HTML dari teks artikel
from datetime import datetime  # Membuat objek datetime dari hasil parsing feed

import requests  # Library HTTP untuk request dengan custom user-agent
import feedparser  # Library untuk membaca/mengurai feed RSS/Atom

from config import RSS_FEEDS  # Daftar feed yang akan di-scrape (dari config)
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
    
    if any(k in text for k in ["sumut", "sumbar", "riau", "lampung", "sumsel", "sumatera", "sumatra", "medan", "padang", "pekanbaru", "palembang", "bengkulu", "jambi", "aceh", "babel", "kepulauan riau", "batam", "tanjung pinang"]):
        return "Sumatra"
    elif any(k in text for k in ["jawa", "jakarta", "bandung", "surabaya", "semarang", "yogyakarta", "banten", "jabar", "jateng", "jatim"]):
        return "Jawa"
    elif any(k in text for k in ["kalimantan", "kaltim", "kalsel", "kalbar", "kalteng", "kalut", "samarinda", "banjarmasin", "pontianak"]):
        return "Kalimantan"
    elif any(k in text for k in ["sulawesi", "makassar", "manado", "palu", "kendari", "gorontalo", "sulsel", "sulteng"]):
        return "Sulawesi"
    elif any(k in text for k in ["papua", "jayapura", "merauke", "sorong", "timika", "irian"]):
        return "Papua"
    elif any(k in text for k in ["bali", "nusa tenggara", "ntb", "ntt", "kupang", "denpasar"]):
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
        source_name = parsed.feed.get("title", feed_url)
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


def run_scrape_job():
    """Dipanggil oleh scheduler. Ambil semua feed, simpan artikel baru ke DB,
    lalu jalankan detector untuk tiap artikel baru."""
    from detector.detector import evaluate_article  # import lokal, hindari circular import
    from notifier.telegram_bot import send_alert_notification  # import lokal, hindari circular import

    if not RSS_FEEDS:  # Kalau daftar feed kosong
        logger.warning("RSS_FEEDS kosong, tidak ada feed yang di-scrape")  # Log peringatan
        return  # Hentikan fungsi

    db = SessionLocal()  # Buka sesi database
    new_count = 0  # Penghitung jumlah artikel baru
    try:
        for feed_url in RSS_FEEDS:  # Loop semua feed yang terdaftar
            try:
                items = fetch_feed(feed_url)  # Ambil daftar artikel dari feed ini
            except Exception:  # Feed gagal diakses/parsing
                logger.exception(f"Feed gagal diakses: {feed_url}")  # Log error lengkap dengan traceback
                continue  # Lewati feed ini, lanjut ke feed berikutnya
            for item in items:  # Loop tiap artikel dari feed tersebut
                if not item["link"]:  # Artikel tanpa link tidak berguna
                    continue  # Skip artikel ini
                exists = db.query(Article).filter(Article.link == item["link"]).first()  # Cek apakah link sudah pernah masuk DB
                if exists:  # Link sudah ada → duplikat
                    continue  # Skip, jangan simpan dua kali
                article = Article(**item)  # Buat objek model dari dict item (key-nya sesuai nama kolom)
                db.add(article)  # Daftarkan objek ke sesi
                db.commit()  # Simpan permanen ke database
                db.refresh(article)  # Muat ulang agar mendapatkan id dari database
                new_count += 1  # Tambah penghitung artikel baru

                try:
                    alert = evaluate_article(db, article)  # Jalankan detector untuk artikel baru ini
                    if alert:  # Artikel lolos threshold → kirim notifikasi Telegram
                        send_alert_notification(article, alert)  # Kirim alert ke Telegram
                except Exception:  # Proses deteksi gagal
                    db.rollback()  # Batalkan perubahan yang belum ter-commit
                    logger.exception(f"Gagal memproses artikel: {item.get('title', 'unknown')}")  # Log error

        logger.info(f"Scrape job selesai. {new_count} artikel baru diproses.")  # Log ringkasan hasil
    finally:
        db.close()  # Tutup sesi database walau ada error
