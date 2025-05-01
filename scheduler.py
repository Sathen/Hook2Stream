from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import database
from database import get_media_added_more_than
from logger import get_logger
from service.radarr_service import handle_ranarr_media
from service.sonarr_service import handle_sonarr_media

logger = get_logger(__name__)


scheduler = AsyncIOScheduler()
job_is_running = False


async def grab_job():
    global job_is_running

    if job_is_running:
        logger.info("[Grab Job] Previous job still running. Skipping new launch.")
        return

    job_is_running = True
    logger.info("[Grab Job] Running scheduled grab job...")
    media_list = get_media_added_more_than(3)

    if not media_list:
        logger.info("[Grab Job] No media found to grab.")
        job_is_running = False
        return
    try:
        for media in media_list:
            logger.info(f"[Grab Job] Need to grab: {media.series_title} added at {media.created_on}")

            if media.source_type == 'SONARR':
                await handle_sonarr_media(media)
            if media.source_type == 'RADARR':
                await handle_ranarr_media(media)

            logger.info(f"[Grab Job] Finished with {media.series_title} push to delete.")
            database.delete_from_db_by_ids(media.internal_id, media.tmdb_id, media.imdb_id, media.tvdb_id)

    except Exception as e:
        logger.error(f"[Grab Job] Error: {e}")
        database.delete_from_db_by_ids(media.internal_id, media.tmdb_id, media.imdb_id, media.tvdb_id)

    finally:
        job_is_running = False
        logger.info("[Grab Job] Finished.")


async def start_grab_scheduler():
    scheduler.add_job(grab_job, IntervalTrigger(minutes=5))
    scheduler.start()
    logger.info("[Scheduler] Started Grab Job every 5 minutes")


async def shutdown():
    scheduler.shutdown()
    logger.info("[Scheduler] Shutdown")
