# api/main.py — API & dashboard web berbasis FastAPI
import logging  # Untuk menulis log
from datetime import datetime, timezone  # datetime & timezone untuk mencatat waktu startup

from fastapi import FastAPI, Depends, Request, Query  # FastAPI: web framework; Depends: injeksi dependency; Request: objek request; Query: validasi query param
from fastapi.middleware.cors import CORSMiddleware  # Middleware untuk mengizinkan akses lintas domain (CORS)
from fastapi.responses import HTMLResponse  # Tipe respons untuk halaman HTML
from fastapi.templating import Jinja2Templates  # Render template HTML
from sqlalchemy.orm import Session  # Tipe sesi database untuk dependency

from auth_utils import hash_password, verify_password  # Hash & verifikasi password (format sama dengan seeder)
from config import LEVEL_RANGES  # Rentang skor untuk level alert 1-5
from database import get_db, init_db  # get_db: dependency sesi DB; init_db: buat tabel
from models.tables import Alert, Article, User  # Model tabel
from scheduler import start_scheduler  # Fungsi untuk menyalakan scheduler
from pydantic import BaseModel
import secrets

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


def _filter_by_level(query, level: int | None):
    """Batasi query alert ke rentang skor sesuai level 1-5."""
    if level is None:
        return query
    lower, upper = LEVEL_RANGES[level]
    query = query.filter(Alert.severity_score >= lower)
    if upper is not None:
        query = query.filter(Alert.severity_score < upper)
    return query


@app.on_event("startup")  # Decorator: fungsi ini dipanggil otomatis saat aplikasi dinyalakan
def on_startup():
    init_db()  # Buat tabel-tabel di database kalau belum ada
    start_scheduler()  # Nyalakan scheduler untuk scraping berkala
    # Jalankan scrape pertama di background agar startup server tidak terblokir
    import threading
    def initial_scrape():
        from scraper.scraper import run_scrape_job
        try:
            run_scrape_job()
        except Exception:
            logging.exception("Scrape awal gagal, scheduler akan coba lagi nanti")
    threading.Thread(target=initial_scrape, daemon=True).start()


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
def list_alerts(
    level: int | None = Query(None, ge=1, le=5),  # Filter level 1-5 (opsional)
    limit: int = 50,  # Jumlah maksimal alert yang dikembalikan
    db: Session = Depends(get_db),  # Sesi database
):
    alerts = (  # Ambil daftar alert paling baru, sudah difilter level jika diminta
        _filter_by_level(db.query(Alert).join(Article), level)
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
            "level": a.level,  # Level alert 1-5 (dihitung dari skor)
            "matched_categories": a.matched_categories,  # Kategori yang cocok
            "matched_words": a.matched_words,  # Kata kunci yang cocok
            "created_at": a.created_at.isoformat(),  # Waktu alert dibuat (format ISO)
        }
        for a in alerts
    ]


@app.get("/", response_class=HTMLResponse)  # Endpoint GET: halaman dashboard utama
def dashboard(
    request: Request,  # Objek request (wajib untuk template)
    level: int | None = Query(None, ge=1, le=5),  # Filter level 1-5 (opsional)
    db: Session = Depends(get_db),  # Sesi database
):
    query = _filter_by_level(db.query(Alert).join(Article), level)  # Query dasar, sudah difilter level
    alerts = (  # Ambil 50 alert terbaru sesuai filter
        query.order_by(Alert.created_at.desc())  # Urutkan dari yang paling baru
        .limit(50)  # Maksimal 50 hasil
        .all()  # Eksekusi query
    )
    matching_alerts = query.count()  # Jumlah seluruh alert yang cocok dengan filter
    total_alerts = db.query(Alert).count()  # Total alert tanpa filter, untuk ringkasan
    total_articles = db.query(Article).count()  # Hitung total artikel untuk ditampilkan di dashboard
    return templates.TemplateResponse(  # Render template HTML
        "dashboard.html",  # Nama file template
        {
            "request": request,  # Objek request (wajib untuk Jinja2)
            "alerts": alerts,  # Data alert yang diteruskan ke template
            "selected_level": level,  # Level yang sedang dipilih di filter
            "matching_alerts": matching_alerts,  # Jumlah alert hasil filter
            "total_alerts": total_alerts,  # Total alert sebelum filter
            "total_articles": total_articles,  # Total artikel yang diteruskan ke template
        },
    )


# --- Authentication & User Management (CRUD Admin, Staff, dll) ---

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str | None = None
    password: str
    role: str = "staff"
    is_active: int | bool = 1

class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    role: str | None = None
    is_active: int | bool | None = None


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Username atau password salah")
    if not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Akun dinonaktifkan")
    token = secrets.token_hex(32)
    return {
        "success": True,
        "message": "Login berhasil",
        "token": token,
        "access_token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
    }


@app.post("/api/auth/logout")
def logout():
    return {
        "success": True,
        "message": "Logout berhasil"
    }


@app.post("/api/auth/register")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
    
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=int(payload.is_active) if payload.is_active is not None else 1
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "success": True,
        "message": "Registrasi berhasil",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
    }


@app.get("/api/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": bool(u.is_active),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@app.post("/api/users")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
    
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=int(payload.is_active) if payload.is_active is not None else 1
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"success": True, "message": "User berhasil dibuat", "id": user.id}


@app.get("/api/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": bool(user.is_active),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@app.put("/api/users/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    if payload.username is not None:
        user.username = payload.username
    if payload.email is not None:
        user.email = payload.email
    if payload.password is not None and payload.password.strip():
        user.hashed_password = hash_password(payload.password)
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = int(payload.is_active)
        
    db.commit()
    return {"success": True, "message": "User berhasil diperbarui"}


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    db.delete(user)
    db.commit()
    return {"success": True, "message": "User berhasil dihapus"}


# --- Regional News & Sources API (Berita Berdasarkan Wilayah seperti Sumatra, dll) ---

@app.get("/api/articles")
def list_articles(
    region: str | None = None,
    source: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Article)
    if region:
        query = query.filter(Article.region.ilike(f"%{region}%"))
    if source:
        query = query.filter(Article.source.ilike(f"%{source}%"))
    if search:
        query = query.filter(Article.title.ilike(f"%{search}%") | Article.raw_summary.ilike(f"%{search}%"))
        
    total = query.count()
    articles = query.order_by(Article.scraped_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "link": a.link,
                "source": a.source,
                "region": a.region,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "scraped_at": a.scraped_at.isoformat() if a.scraped_at else None,
                "raw_summary": a.raw_summary,
            }
            for a in articles
        ]
    }


@app.get("/api/regions")
def get_regions(db: Session = Depends(get_db)):
    from sqlalchemy import func
    results = db.query(Article.region, func.count(Article.id)).group_by(Article.region).all()
    return [{"region": r[0] or "Nasional", "count": r[1]} for r in results]


@app.get("/api/sources")
def get_sources(db: Session = Depends(get_db)):
    from sqlalchemy import func
    results = db.query(Article.source, func.count(Article.id)).group_by(Article.source).all()
    return [{"source": r[0] or "Unknown", "count": r[1]} for r in results]


# --- Scraper Control API (Start, Stop, Status, Run Now) ---

@app.get("/api/scraper/status")
def scraper_status():
    from scheduler import get_scheduler_status
    return get_scheduler_status()


@app.post("/api/scraper/start")
def start_scraper_job():
    from scheduler import start_scheduler
    start_scheduler()
    return {"success": True, "message": "Scraper berhasil dijalankan (start)"}


@app.post("/api/scraper/stop")
def stop_scraper_job():
    from scheduler import stop_scheduler
    stop_scheduler()
    return {"success": True, "message": "Scraper berhasil dihentikan (stop)"}


@app.post("/api/scraper/run-now")
def run_scraper_now():
    from scheduler import trigger_manual_scrape
    trigger_manual_scrape()
    return {"success": True, "message": "Scraping manual segera dijalankan di background"}
