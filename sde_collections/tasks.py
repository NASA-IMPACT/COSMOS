from config import celery_app
from sde_scraper.runner import run_scraper


@celery_app.task()
def generate_candidate_urls_async(name, url):
    """Generate candidate urls using celery."""
    run_scraper(name, url)
