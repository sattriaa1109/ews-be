# api/main.py — API & dashboard web berbasis FastAPI
import logging  # Untuk menulis log
from datetime import datetime, timezone  # datetime & timezone untuk mencatat waktu startup

from fastapi import FastAPI, Depends, Request  # FastAPI: web framework; Depends: injeksi dependency; Request: objek request
from fastapi.middleware.cors import CORSMiddleware  # Middleware untuk mengizinkan akses lintas domain (CORS)
from fastapi.responses import HTMLResponse  # Tipe respons untuk halaman HTML
from fastapi.templating import Jinja2Templates  # Render template HTML
from sqlalchemy.orm import Session  # Tipe sesi database untuk dependency

from database import get_db, init_db  # get_db: dependency sesi DB; init_db: buat tabel
from models.tables import Alert, Article  # Model tabel
from scheduler import start_scheduler  # Fungsi untuk menyalakan scheduler

logging.basicConfig(level=logging.INFO)  # Set level log ke INFO agar log terlihat di konsol

app = FastAPI(title="EWS Monitoring Media - TNI AD")  # Buat instance aplikasi FastAPI
templates = Jinja2Templates(directory="templates")  # Siapkan folder tempat template HTML disimpan

# Izinkan frontend (React/Vue/dll) di port lain memanggil API ini
app.add_middleware(  # Daftarkan middleware CORS ke aplikasi
    CORSMiddleware,
    allow_origins=["*"],  # Izinkan semua asal (origin) request
    allow_credentials=True,  # Izinkan pengiriman cookie/kredensial
    allow_methods=["*"],  # Izinkan semua metode HTTP (GET, POST, dll)
    allow_headers=["*"],  # Izinkan semua header
)

# Simpan waktu startup buat status "uptime sejak"
APP_STARTED_AT = datetime.now(timezone.utc)  # Catat waktu aplikasi mulai (dalam UTC)


@app.on_event("startup")  # Decorator: fungsi ini dipanggil otomatis saat aplikasi dinyalakan
def on_startup():
    init_db()  # Buat tabel-tabel di database kalau belum ada
    start_scheduler()  # Nyalakan scheduler untuk scraping berkala
    # Jalankan scrape pertama segera, tidak perlu nunggu interval
    from scraper.scraper import run_scrape_job  # Import lokal (dilakukan di sini untuk menghindari import berantai)
    try:
        run_scrape_job()  # Langsung jalankan satu kali scraping saat aplikasi start
    except Exception:  # Jika scrape awal gagal
        logging.exception("Scrape awal gagal, scheduler akan coba lagi nanti")  # Log error, scheduler tetap jadi cadangan


@app.get("/api/status")  # Endpoint GET: cek status aplikasi
def get_status(db: Session = Depends(get_db)):  # Dependency membuka sesi database otomatis
    total_articles = db.query(Article).count()  # Hitung jumlah total artikel
    total_alerts = db.query(Alert).count()  # Hitung jumlah total alert
    last_article = (  # Cari artikel yang terakhir kali di-scrape
        db.query(Article).order_by(Article.scraped_at.desc()).first()  # Urutkan dari scrape terbaru, ambil yang paling atas
    )
    return {  # Balasan JSON berisi informasi status
        "status": "running",  # Status aplikasi
        "started_at": APP_STARTED_AT.isoformat(),  # Waktu mulai aplikasi (format ISO)
        "total_articles_scraped": total_articles,  # Jumlah total artikel
        "total_alerts": total_alerts,  # Jumlah total alert
        "last_scrape_at": last_article.scraped_at.isoformat() if last_article else None,  # Waktu scrape terakhir, atau null jika belum ada
    }


@app.get("/api/alerts")  # Endpoint GET: daftar alert
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):  # Parameter limit (default 50) + sesi database
    alerts = (  # Ambil daftar alert paling baru
        db.query(Alert)  # Query tabel alert
        .join(Article)  # Gabung dengan tabel articles
        .order_by(Alert.created_at.desc())  # Urutkan dari yang paling baru
        .limit(limit)  # Batasi jumlah hasil
        .all()  # Eksekusi query
    )
    return [  # Ubah tiap record alert jadi dict untuk respons JSON
        {
            "id": a.id,  # ID alert
            "title": a.article.title,  # Judul artikel terkait
            "link": a.article.link,  # Link artikel terkait
            "source": a.article.source,  # Nama sumber
            "severity_score": a.severity_score,  # Skor keparahan
            "matched_categories": a.matched_categories,  # Kategori yang cocok
            "matched_words": a.matched_words,  # Kata kunci yang cocok
            "notified": bool(a.notified),  # Status sudah dikirim notifikasi (diubah jadi boolean)
            "created_at": a.created_at.isoformat(),  # Waktu alert dibuat (format ISO)
        }
        for a in alerts
    ]


@app.get("/", response_class=HTMLResponse)  # Endpoint GET: halaman dashboard utama
def dashboard(request: Request, db: Session = Depends(get_db)):  # Request dibutuhkan untuk template + sesi database
    alerts = (  # Ambil 50 alert terbaru (query sama seperti /api/alerts)
        db.query(Alert)  # Query tabel alert
        .join(Article)  # Gabung dengan tabel articles
        .order_by(Alert.created_at.desc())  # Urutkan dari yang paling baru
        .limit(50)  # Maksimal 50 hasil
        .all()  # Eksekusi query
    )
    total_articles = db.query(Article).count()  # Hitung total artikel untuk ditampilkan di dashboard
    return templates.TemplateResponse(  # Render template HTML
        "dashboard.html",  # Nama file template
        {
            "request": request,  # Objek request (wajib untuk Jinja2)
            "alerts": alerts,  # Data alert yang diteruskan ke template
            "total_articles": total_articles,  # Total artikel yang diteruskan ke template
        },
    )
