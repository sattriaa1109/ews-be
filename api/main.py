import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db, init_db
from models.tables import Alert, Article
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EWS Monitoring Media - TNI AD")
templates = Jinja2Templates(directory="templates")

# Izinkan frontend (React/Vue/dll) di port lain memanggil API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simpan waktu startup buat status "uptime sejak"
APP_STARTED_AT = datetime.now(timezone.utc)


@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()
    # Jalankan scrape pertama segera, tidak perlu nunggu interval
    from scraper.scraper import run_scrape_job
    try:
        run_scrape_job()
    except Exception:
        logging.exception("Scrape awal gagal, scheduler akan coba lagi nanti")


@app.get("/api/status")
def get_status(db: Session = Depends(get_db)):
    total_articles = db.query(Article).count()
    total_alerts = db.query(Alert).count()
    last_article = (
        db.query(Article).order_by(Article.scraped_at.desc()).first()
    )
    return {
        "status": "running",
        "started_at": APP_STARTED_AT.isoformat(),
        "total_articles_scraped": total_articles,
        "total_alerts": total_alerts,
        "last_scrape_at": last_article.scraped_at.isoformat() if last_article else None,
    }


@app.get("/api/alerts")
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert)
        .join(Article)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "title": a.article.title,
            "link": a.article.link,
            "source": a.article.source,
            "severity_score": a.severity_score,
            "matched_categories": a.matched_categories,
            "matched_words": a.matched_words,
            "notified": bool(a.notified),
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert)
        .join(Article)
        .order_by(Alert.created_at.desc())
        .limit(50)
        .all()
    )
    total_articles = db.query(Article).count()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "alerts": alerts,
            "total_articles": total_articles,
        },
    )
