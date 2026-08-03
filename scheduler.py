# scheduler.py — Menjalankan job scraping secara berkala di background
import logging  # Untuk menulis log

from apscheduler.schedulers.background import BackgroundScheduler  # Scheduler yang berjalan di thread background

from config import SCRAPE_INTERVAL_MINUTES  # Interval scrape dari config
from scraper.scraper import run_scrape_job  # Fungsi yang akan dijalankan scheduler

logger = logging.getLogger("scheduler")  # Logger khusus untuk modul scheduler

scheduler = BackgroundScheduler()  # Buat instance scheduler background


def start_scheduler():
    scheduler.add_job(  # Daftarkan job ke scheduler
        run_scrape_job,  # Fungsi yang dipanggil tiap interval
        "interval",  # Jenis jadwal: berulang setiap interval waktu
        minutes=SCRAPE_INTERVAL_MINUTES,  # Interval dalam menit
        id="scrape_job",  # ID unik untuk job ini
    )
    scheduler.start()  # Mulai scheduler
    logger.info(f"Scheduler aktif, scraping tiap {SCRAPE_INTERVAL_MINUTES} menit.")  # Log bahwa scheduler berjalan
