import asyncio

import download
from download import download_videos
from logger import get_logger
from models import MediaData
from search_links import search_film
from sonarr import tell_radarr_manual_import

logger = get_logger(__name__)


async def handle_ranarr_media(media: MediaData):
    logger.info(f"[Radarr service] Find movie: {media.series_title}")

    video_links = search_film(media)

    path = await asyncio.to_thread(download_videos, media.local_title, video_links)

    if not download.is_aborted():
        await tell_radarr_manual_import(media, path)
