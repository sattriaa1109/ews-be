# notifier/telegram_bot.py — Mengirim notifikasi alert ke Telegram
import logging  # Untuk menulis log
from html import escape  # Escape karakter HTML agar judul/sumber yang aneh tidak merusak format

import requests  # Library HTTP untuk memanggil API Telegram

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  # Kredensial Telegram dari config
from database import SessionLocal  # Pabrik sesi database
from models.tables import Alert  # Model tabel alert

logger = logging.getLogger("notifier")  # Logger khusus untuk modul notifier

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"  # Template URL API Telegram untuk kirim pesan


def _build_message(article, alert) -> str:
    """Menyusun teks pesan notifikasi berisi info artikel & alert."""
    link = article.link.replace('&', '&amp;')  # URL perlu di-escape agar valid di atribut HTML
    return (  # Bangun teks (format HTML Telegram) dengan f-string agar nilainya langsung dimasukkan
        f"⚠️ <b>PERINGATAN PEMBERITAAN</b>\n\n"  # Baris header peringatan
        f"<b>Judul:</b> {escape(article.title)}\n"  # Baris judul artikel
        f"<b>Sumber:</b> {escape(article.source)}\n"  # Baris nama sumber
        f"<b>Skor Severity:</b> {alert.severity_score}\n"  # Baris skor keparahan
        f"<b>Kategori:</b> {escape(alert.matched_categories)}\n"  # Baris kategori yang cocok
        f"<b>Kata terdeteksi:</b> {escape(alert.matched_words)}\n\n"  # Baris kata kunci yang cocok
        f'<a href="{link}">Baca artikel</a>'  # Link artikel (bisa diklik)
    )


def send_alert_notification(article, alert) -> bool:
    """Kirim alert ke Telegram. Kalau berhasil, tandai alert.notified = 1."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:  # Kredensial belum di-set
        logger.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum di-set, alert tidak dikirim.")  # Log peringatan
        return False  # Gagal kirim

    url = TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN)  # Isi token ke dalam template URL
    payload = {  # Body request yang dikirim ke API Telegram
        "chat_id": TELEGRAM_CHAT_ID,  # ID chat penerima pesan
        "text": _build_message(article, alert),  # Isi pesan yang sudah disusun
        "parse_mode": "HTML",  # Format pesan menggunakan HTML
        "disable_web_page_preview": False,  # Tampilkan preview link artikel
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)  # Kirim request POST, timeout 10 detik
        resp.raise_for_status()  # Lempar error jika status bukan 2xx

        db = SessionLocal()  # Buka sesi database
        try:
            db_alert = db.query(Alert).filter(Alert.id == alert.id).first()  # Ambil ulang alert dari database
            if db_alert:  # Record ditemukan
                db_alert.notified = 1  # Tandai alert sudah dikirim notifikasi
                db.commit()  # Simpan perubahan ke database
        finally:
            db.close()  # Tutup sesi database

        return True  # Kirim berhasil
    except requests.RequestException as e:  # Error jaringan/HTTP saat memanggil API
        logger.error(f"Gagal kirim notifikasi Telegram: {e}")  # Log error
        return False  # Gagal kirim
