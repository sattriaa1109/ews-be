import logging

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from database import SessionLocal
from models.tables import Alert

logger = logging.getLogger("notifier")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _build_message(article, alert) -> str:
    return (
        f"⚠️ *PERINGATAN PEMBERITAAN*\n\n"
        f"*Judul:* {article.title}\n"
        f"*Sumber:* {article.source}\n"
        f"*Skor Severity:* {alert.severity_score}\n"
        f"*Kategori:* {alert.matched_categories}\n"
        f"*Kata terdeteksi:* {alert.matched_words}\n\n"
        f"[Baca artikel]({article.link})"
    )


def send_alert_notification(article, alert) -> bool:
    """Kirim alert ke Telegram. Kalau berhasil, tandai alert.notified = 1."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum di-set, alert tidak dikirim.")
        return False

    url = TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": _build_message(article, alert),
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()

        db = SessionLocal()
        try:
            db_alert = db.query(Alert).filter(Alert.id == alert.id).first()
            if db_alert:
                db_alert.notified = 1
                db.commit()
        finally:
            db.close()

        return True
    except requests.RequestException as e:
        logger.error(f"Gagal kirim notifikasi Telegram: {e}")
        return False
