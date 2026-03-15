from celery import Celery
from celery.schedules import crontab
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "skillpack",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,  # one task at a time (crawlers are heavy)
    beat_schedule={
        # Full crawl every day at 2am UTC
        "daily-crawl": {
            "task": "workers.tasks.run_full_crawl",
            "schedule": crontab(hour=2, minute=0),
        },
        # Regenerate bundles every day at 4am UTC (after crawl finishes)
        "daily-bundle-regen": {
            "task": "workers.tasks.regenerate_bundles",
            "schedule": crontab(hour=4, minute=0),
        },
    },
)
