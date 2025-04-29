import logging

from database import add_to_db, delete_from_db_by_ids, get_monitored_seasons
from localization import get_ukrainian_title

logging.basicConfig(level=logging.INFO)


async def delete_media(media_data):
    if media_data.tmdb_id or media_data.imdb_id or media_data.tvdb_id:
        delete_from_db_by_ids(
            internal_id=media_data.internal_id,
            tmdbId=media_data.tmdb_id,
            imdbId=media_data.imdb_id,
            tvdbId=media_data.tvdb_id
        )
        logging.info(
            f"Deleted {media_data.series_title} with tmdb: {media_data.tmdb_id}, imdb: {media_data.imdb_id}, tvdb: {media_data.tvdb_id}")
    else:
        logging.info(f"No valid ID provided for {media_data.event_type} event for title {media_data.series_title}")


async def add_media(body_json, media_data):
    logging.info(f"SeriesAdd Event Body: {body_json}")
    seasons = await get_monitored_seasons(media_data.internal_id)
    local_title = await get_ukrainian_title(media_data.tmdb_id)
    add_to_db(
        media_data.internal_id,
        media_data.series_title,
        media_data.date,
        media_data.tmdb_id,
        media_data.imdb_id,
        media_data.tvdb_id,
        seasons,
        local_title
    )
    logging.info(
        f"Added {media_data.series_title} with tmdb: {media_data.tmdb_id}, imdb: {media_data.imdb_id}, tvdb: {media_data.tvdb_id}")
