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

# Sumber berita default (RSS) yang selalu ikut di-scrape.
# RSS_FEEDS di .env bersifat tambahan, jadi sumber di bawah ini tetap aktif
# walaupun operator hanya mengisi sedikit feed di .env.
DEFAULT_RSS_FEEDS = [
    # Media nasional
    "https://www.antaranews.com/rss/terkini.xml",       # ANTARA News — terkini
    "https://www.antaranews.com/rss/hukum.xml",         # ANTARA News — hukum
    "https://www.antaranews.com/rss/politik.xml",       # ANTARA News — politik
    "https://www.antaranews.com/rss/ekonomi.xml",       # ANTARA News — ekonomi
    "https://www.cnnindonesia.com/rss",                 # CNN Indonesia
    "https://www.sindonews.com/rss",                    # Sindonews
    "https://nasional.sindonews.com/rss",               # Sindonews — nasional
    "https://www.cnbcindonesia.com/rss",                # CNBC Indonesia
    "https://www.tribunnews.com/rss",                   # Tribunnews
    "https://www.jpnn.com/rss",                         # JPNN
    "https://www.inews.id/feed",                        # iNews
    "https://katadata.co.id/rss",                       # Katadata
    # Instansi pemerintah / penegak hukum
    "https://www.kemhan.go.id/feed",                    # Kementerian Pertahanan
    "https://www.bnn.go.id/feed",                       # Badan Narkotika Nasional
    # Google News — agregator + pencarian kata kunci sensitif
    "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=TNI+AD&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=Kodam&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=TNI+Angkatan+Darat&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=Kemhan&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=Oknum+TNI&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=Prajurit+TNI&hl=id&gl=ID&ceid=ID:id",
]

# RSS feed regional ANTARA, dikelompokkan per pulau/wilayah.
REGIONAL_RSS_FEEDS = [
    # Sumatra
    "https://aceh.antaranews.com/rss/terkini.xml",
    "https://sumut.antaranews.com/rss/terkini.xml",
    "https://sumbar.antaranews.com/rss/terkini.xml",
    "https://riau.antaranews.com/rss/terkini.xml",
    "https://kepri.antaranews.com/rss/terkini.xml",
    "https://jambi.antaranews.com/rss/terkini.xml",
    "https://bengkulu.antaranews.com/rss/terkini.xml",
    "https://sumsel.antaranews.com/rss/terkini.xml",
    "https://babel.antaranews.com/rss/terkini.xml",
    "https://lampung.antaranews.com/rss/terkini.xml",
    # Jawa
    "https://jabar.antaranews.com/rss/terkini.xml",
    "https://jateng.antaranews.com/rss/terkini.xml",
    "https://jatim.antaranews.com/rss/terkini.xml",
    # Bali & Nusa Tenggara
    "https://bali.antaranews.com/rss/terkini.xml",
    "https://mataram.antaranews.com/rss/terkini.xml",
    "https://kupang.antaranews.com/rss/terkini.xml",
    # Kalimantan
    "https://kaltim.antaranews.com/rss/terkini.xml",
    "https://kalteng.antaranews.com/rss/terkini.xml",
    "https://kalbar.antaranews.com/rss/terkini.xml",
    "https://kalsel.antaranews.com/rss/terkini.xml",
    # Sulawesi
    "https://makassar.antaranews.com/rss/terkini.xml",
    "https://manado.antaranews.com/rss/terkini.xml",
    "https://sulteng.antaranews.com/rss/terkini.xml",
    "https://sultra.antaranews.com/rss/terkini.xml",
    # Maluku & Papua
    "https://ambon.antaranews.com/rss/terkini.xml",
    "https://papua.antaranews.com/rss/terkini.xml",
]

# Gabungkan: feed dari .env didahulukan, lalu default & regional tanpa duplikat.
RSS_FEEDS = [
    url.strip()  # Bersihkan spasi di awal/akhir tiap URL
    for url in os.getenv("RSS_FEEDS", "").split(",")  # Ambil nilai RSS_FEEDS dari .env, pecah per koma
    if url.strip()  # Abaikan item yang kosong setelah di-trim
]

for feed in DEFAULT_RSS_FEEDS + REGIONAL_RSS_FEEDS:
    if feed not in RSS_FEEDS:
        RSS_FEEDS.append(feed)

# Jumlah worker paralel saat mengunduh feed (biar siklus scrape tidak terlalu lama).
SCRAPER_MAX_WORKERS = int(os.getenv("SCRAPER_MAX_WORKERS", "8"))

# Google Custom Search Engine (Programmable Search Engine) API.
# Isi GOOGLE_CSE_API_KEY dan GOOGLE_CSE_ID di .env untuk mengaktifkan sumber ini.
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "").strip()
# Query pencarian untuk CSE (pisahkan dengan koma). Default berfokus ke TNI AD.
GOOGLE_CSE_QUERIES = [
    q.strip()
    for q in os.getenv(
        "GOOGLE_CSE_QUERIES",
        "TNI AD, Kodam, TNI Angkatan Darat, Oknum TNI, Prajurit TNI",
    ).split(",")
    if q.strip()
]
# Jumlah hasil per query (maks 10 per request sesuai batas API Google CSE).
GOOGLE_CSE_NUM_RESULTS = int(os.getenv("GOOGLE_CSE_NUM_RESULTS", "10"))

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
