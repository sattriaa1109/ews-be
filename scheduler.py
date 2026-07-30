import logging

from apscheduler.schedulers.background import BackgroundScheduler

from config import SCRAPE_INTERVAL_MINUTES
from scraper.scraper import run_scrape_job

logger = logging.getLogger("scheduler")

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        run_scrape_job,
        "interval",
        minutes=SCRAPE_INTERVAL_MINUTES,
        id="scrape_job",
    )
    scheduler.start()
    logger.info(f"Scheduler aktif, scraping tiap {SCRAPE_INTERVAL_MINUTES} menit.")
