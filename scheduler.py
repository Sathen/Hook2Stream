from enum import Enum
from typing import List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import database
from database import get_media_added_more_than
from logger import get_logger
from models import MediaData
from service.radarr_service import handle_ranarr_media
from service.sonarr_service import handle_sonarr_media

logger = get_logger(__name__)

# Constants
CHECK_INTERVAL_MINUTES = 5
MEDIA_AGE_MINUTES = 3


class MediaSourceType(Enum):
    """Media source types supported by the scheduler."""
    SONARR = "SONARR"
    RADARR = "RADARR"


class GrabScheduler:
    """Manages scheduled media grabbing jobs."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._job_is_running = False
        self._handlers = {
            MediaSourceType.SONARR: handle_sonarr_media,
            MediaSourceType.RADARR: handle_ranarr_media
        }

    async def _grab_job(self) -> None:
        """Execute the media grab job."""
        if self._job_is_running:
            logger.info("[Grab Job] Previous job still running. Skipping new launch.")
            return

        try:
            self._job_is_running = True
            await self._process_media_list()
        finally:
            self._job_is_running = False
            logger.info("[Grab Job] Finished.")

    async def _process_media_list(self) -> None:
        """Process all pending media items."""
        logger.info("[Grab Job] Running scheduled grab job...")
        media_list = get_media_added_more_than(MEDIA_AGE_MINUTES)

        if not media_list:
            logger.info("[Grab Job] No media found to grab.")
            return

        for media in media_list:
            await self._process_single_media(media)

    async def _process_single_media(self, media: MediaData) -> None:
        """Process a single media item."""
        try:
            logger.info(f"[Grab Job] Processing: {media.series_title} (added at {media.created_on})")
            
            source_type = MediaSourceType(media.source_type)
            handler = self._handlers.get(source_type)
            
            if handler:
                await handler(media)
                logger.info(f"[Grab Job] Finished processing {media.series_title}")
            else:
                logger.error(f"[Grab Job] Unknown source type: {media.source_type}")
                
        except Exception as e:
            logger.error(f"[Grab Job] Error processing {media.series_title}: {e}")
        finally:
            self._cleanup_media(media)

    def _cleanup_media(self, media: MediaData) -> None:
        """Clean up media entry from database."""
        database.delete_from_db_by_ids(
            internal_id=media.internal_id,
            tmdb_id=media.tmdb_id,
            imdb_id=media.imdb_id,
            tvdb_id=media.tvdb_id
        )

    async def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.add_job(
            self._grab_job,
            IntervalTrigger(minutes=CHECK_INTERVAL_MINUTES)
        )
        self.scheduler.start()
        logger.info(f"[Scheduler] Started Grab Job every {CHECK_INTERVAL_MINUTES} minutes")

    async def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("[Scheduler] Shutdown")


# Create singleton instance
scheduler = GrabScheduler()

# Public API
async def start_grab_scheduler() -> None:
    """Start the grab scheduler."""
    await scheduler.start()

async def shutdown() -> None:
    """Shutdown the scheduler."""
    await scheduler.shutdown()
