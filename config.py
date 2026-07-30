import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ews_local.db")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "15"))

RSS_FEEDS = [
    url.strip()
    for url in os.getenv("RSS_FEEDS", "").split(",")
    if url.strip()
]

# Kata kunci konteks: artikel harus mengandung minimal salah satu ini
# supaya dianggap relevan (mengurangi false positive)
CONTEXT_KEYWORDS = [
    "TNI AD", "TNI Angkatan Darat", "Kodam", "Prajurit TNI", "Kopassus",
    "Kostrad", "Babinsa", "Danrem", "Panglima TNI",
]

# Kata kunci negatif/sensitif per kategori, tiap kategori punya bobot
NEGATIVE_KEYWORDS = {
    "pelanggaran_hukum": {
        "words": ["korupsi", "penyalahgunaan wewenang", "suap", "pungli", "penggelapan"],
        "weight": 3,
    },
    "kekerasan": {
        "words": ["kekerasan", "penganiayaan", "penembakan", "baku tembak", "bentrok"],
        "weight": 3,
    },
    "ham": {
        "words": ["pelanggaran HAM", "penyiksaan", "hilang paksa", "intimidasi warga"],
        "weight": 4,
    },
    "disiplin_internal": {
        "words": ["desersi", "oknum", "dipecat", "sidang disiplin", "sanksi"],
        "weight": 2,
    },
    "isu_viral": {
        "words": ["viral", "ramai diperbincangkan", "trending", "heboh"],
        "weight": 1,
    },
}

# Skor minimum supaya artikel dikirim sebagai alert
ALERT_THRESHOLD = 3
