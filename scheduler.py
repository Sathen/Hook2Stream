import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import database
from database import get_media_added_more_than, get_monitored_seasons
from download import download_videos
from search_links import search_film

scheduler = AsyncIOScheduler()
job_is_running = False


async def grab_job():
    global job_is_running

    if job_is_running:
        logging.info("[Grab Job] Previous job still running. Skipping new launch.")
        return

    job_is_running = True
    logging.info("[Grab Job] Running scheduled grab job...")
    media_list = get_media_added_more_than(3)

    if not media_list:
        logging.info("[Grab Job] No media found to grab.")
        return
    try:
        for media in media_list:
            logging.info(f"[Grab Job] Need to grab: {media.series_title} added at {media.date}")
            seasons = get_monitored_seasons(media.internal_id)

            for season in seasons:
                video_links = search_film(media.local_title, season)
                download_videos(media.local_title, season, video_links)

            logging.info(f"Finished with {media.series_title} push to delete.")
            database.delete_from_db_by_ids(media.internal_id, media.tmdb_id, media.imdb_id, media.tvdb_id)

    except Exception as e:
        logging.error(f"[Grab Job] Error: {e}")
    finally:
        job_is_running = False
        logging.info("[Grab Job] Finished.")


async def start_grab_scheduler():
    scheduler.add_job(grab_job, IntervalTrigger(minutes=5))
    scheduler.start()
    logging.info("[Scheduler] Started Grab Job every 5 minutes")


async def shutdown():
    scheduler.shutdown()
    logging.info("[Scheduler] Shutdown")
