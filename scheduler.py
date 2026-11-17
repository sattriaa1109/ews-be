# scheduler.py — Menjalankan job scraping secara berkala di background
import logging  # Untuk menulis log

from apscheduler.schedulers.background import BackgroundScheduler  # Scheduler yang berjalan di thread background

from config import SCRAPE_INTERVAL_MINUTES  # Interval scrape dari config
from scraper.scraper import run_scrape_job  # Fungsi yang akan dijalankan scheduler

logger = logging.getLogger("scheduler")  # Logger khusus untuk modul scheduler

scheduler = BackgroundScheduler()  # Buat instance scheduler background


def start_scheduler():
    if not scheduler.get_job("scrape_job"):
        scheduler.add_job(  # Daftarkan job ke scheduler
            run_scrape_job,  # Fungsi yang dipanggil tiap interval
            "interval",  # Jenis jadwal: berulang setiap interval waktu
            minutes=SCRAPE_INTERVAL_MINUTES,  # Interval dalam menit
            id="scrape_job",  # ID unik untuk job ini
            replace_existing=True,
        )
    if not scheduler.running:
        scheduler.start()  # Mulai scheduler
    else:
        try:
            scheduler.resume()
        except Exception:
            pass
    logger.info(f"Scheduler aktif, scraping tiap {SCRAPE_INTERVAL_MINUTES} menit.")  # Log bahwa scheduler berjalan


def stop_scheduler():
    """Menghentikan/mem-pause scheduler scraping."""
    if scheduler.running:
        try:
            scheduler.pause()
        except Exception:
            pass
    logger.info("Scheduler dihentikan/dipause.")


def get_scheduler_status():
    """Mendapatkan status scheduler (running/stopped, next run time)."""
    is_running = scheduler.running
    job = scheduler.get_job("scrape_job")
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    paused = job.next_run_time is None if job else not is_running
    return {
        "running": is_running and not paused,
        "next_run_time": next_run,
        "interval_minutes": SCRAPE_INTERVAL_MINUTES
    }


def trigger_manual_scrape():
    """Menjalankan scraping secara manual langsung di background thread."""
    import threading
    threading.Thread(target=run_scrape_job, daemon=True).start()
