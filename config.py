# config.py — Pusat konfigurasi aplikasi (membaca pengaturan dari file .env)
import os  # Import modul os untuk membaca variabel lingkungan (environment variable)
from dotenv import load_dotenv  # Import load_dotenv untuk memuat isi file .env ke environment

load_dotenv()  # Jalankan load_dotenv agar semua variabel di file .env tersedia untuk program

# URL koneksi database; kalau DATABASE_URL tidak di-set di .env, pakai default PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ews_user:ews_pass@localhost:5432/ews_db")

# Token bot Telegram untuk mengirim notifikasi; kosong jika belum di-set
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# ID chat Telegram tujuan notifikasi; kosong jika belum di-set
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Interval scrape otomatis dalam menit; default 15, lalu diubah tipe datanya jadi integer
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "15"))

# Daftar RSS feed yang akan di-scrape
RSS_FEEDS = [
    url.strip()  # Bersihkan spasi di awal/akhir tiap URL
    for url in os.getenv("RSS_FEEDS", "").split(",")  # Ambil nilai RSS_FEEDS dari .env, pecah per koma
    if url.strip()  # Abaikan item yang kosong setelah di-trim
]

# Tambahan RSS feed regional (Sumatra & wilayah Indonesia lainnya)
REGIONAL_RSS_FEEDS = [
    "https://sumut.antaranews.com/rss/terkini.xml",
    "https://sumbar.antaranews.com/rss/terkini.xml",
    "https://riau.antaranews.com/rss/terkini.xml",
    "https://lampung.antaranews.com/rss/terkini.xml",
    "https://sumsel.antaranews.com/rss/terkini.xml",
]

for feed in REGIONAL_RSS_FEEDS:
    if feed not in RSS_FEEDS:
        RSS_FEEDS.append(feed)

# Kata kunci konteks: artikel harus mengandung minimal salah satu ini
# supaya dianggap relevan (mengurangi false positive)
CONTEXT_KEYWORDS = [  # Daftar kata yang menunjukkan artikel menyangkut TNI AD / penegak hukum
    "TNI AD", "TNI Angkatan Darat", "Kodam", "Prajurit TNI", "Kopassus",
    "Kostrad", "Babinsa", "Danrem", "Panglima TNI",
    "TNI", "Pangdam", "Kasad", "teritorial", "Yonif", "Pussenif",
    "Tentara Nasional Indonesia", "Angkatan Darat", "Kemhan",
    "polisi", "KPK", "penegak hukum", "aparat",
]

# Kata kunci negatif/sensitif per kategori, tiap kategori punya bobot
NEGATIVE_KEYWORDS = {  # Kamus kategori berisi kata kunci & bobot penalti
    "pelanggaran_hukum": {  # Kategori: pelanggaran hukum
        "words": ["korupsi", "penyalahgunaan wewenang", "suap", "pungli", "penggelapan"],  # Kata-kata yang dideteksi
        "weight": 3,  # Bobot skor per kata
    },
    "kekerasan": {  # Kategori: kekerasan
        "words": ["kekerasan", "penganiayaan", "penembakan", "baku tembak", "bentrok"],  # Kata-kata yang dideteksi
        "weight": 3,  # Bobot skor per kata
    },
    "ham": {  # Kategori: pelanggaran HAM
        "words": ["pelanggaran HAM", "penyiksaan", "hilang paksa", "intimidasi warga"],  # Kata-kata yang dideteksi
        "weight": 4,  # Bobot paling tinggi karena paling serius
    },
    "disiplin_internal": {  # Kategori: pelanggaran disiplin internal
        "words": ["desersi", "oknum", "dipecat", "sidang disiplin", "sanksi"],  # Kata-kata yang dideteksi
        "weight": 2,  # Bobot skor per kata
    },
    "isu_viral": {  # Kategori: isu yang sedang viral
        "words": ["viral", "ramai diperbincangkan", "trending", "heboh"],  # Kata-kata yang dideteksi
        "weight": 1,  # Bobot paling kecil
    },
}

# Skor minimum supaya artikel dikirim sebagai alert
ALERT_THRESHOLD = 2  # Artikel baru jadi alert jika skor >= 2
