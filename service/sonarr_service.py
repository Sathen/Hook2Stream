import asyncio

import download
from download import download_videos
from models import MediaData
from search_links import search_film
from sonarr import get_monitored_seasons, tell_sonarr_manual_import
from logger import get_logger

logger = get_logger(__name__)


async def handle_sonarr_media(media: MediaData):
    seasons = list(get_monitored_seasons(media.internal_id))
    logger.info(f"[Sonar service] Find seasons: {seasons} for serial: {media.series_title}")

    for season in seasons:
        video_links = search_film(media, season)

        path = await asyncio.to_thread(download_videos, media.series_title, video_links, season)

        if download.is_aborted():
            await tell_sonarr_manual_import(media, path, season)
