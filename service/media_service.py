import sonarr
from database import add_to_db, delete_from_db_by_ids
from localization import get_ukrainian_title
from models import MediaData

from logger import get_logger

logger = get_logger(__name__)


async def delete_media(media_data: MediaData):
    if media_data.tmdb_id or media_data.imdb_id or media_data.tvdb_id or media_data.internal_id:
        delete_from_db_by_ids(
            internal_id=media_data.internal_id,
            tmdb_id=media_data.tmdb_id,
            imdb_id=media_data.imdb_id,
            tvdb_id=media_data.tvdb_id
        )
        logger.info(
            f"Deleted {media_data.series_title} with "
            f"tmdb: {media_data.tmdb_id}, "
            f"imdb: {media_data.imdb_id}, "
            f"tvdb: {media_data.tvdb_id}")
    else:
        logger.info(f"No valid ID provided for title {media_data.series_title}")


async def add_media(media_data: MediaData):
    logger.info(f"Add Event Body: {media_data}")
    seasons = await sonarr.get_monitored_seasons(media_data.internal_id)
    local_title = await get_ukrainian_title(media_data.tmdb_id)
    media_data.local_title = local_title

    add_to_db(media_data, seasons)

    logger.info(
        f"Added {media_data.series_title} with tmdb: {media_data.tmdb_id}, "
        f"imdb: {media_data.imdb_id}, tvdb: {media_data.tvdb_id}")
