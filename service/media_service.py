from typing import List, Optional
from contextlib import asynccontextmanager

import sonarr
from database import add_to_db, delete_from_db_by_ids
from localization import get_ukrainian_title
from models import MediaData
from logger import get_logger

logger = get_logger(__name__)


class MediaServiceError(Exception):
    """Base exception for media service operations."""
    pass


@asynccontextmanager
async def media_operation_context(operation: str):
    """Context manager for media operations with error handling."""
    try:
        yield
    except Exception as e:
        logger.error(f"Failed to {operation}: {str(e)}")
        raise MediaServiceError(f"Failed to {operation}: {str(e)}")


async def delete_media(media_data: MediaData) -> None:
    """
    Delete media entry from database.
    
    Args:
        media_data: Media data to delete
        
    Raises:
        MediaServiceError: If deletion fails
    """
    async with media_operation_context("delete media"):
        if not any([
            media_data.tmdb_id,
            media_data.imdb_id,
            media_data.tvdb_id,
            media_data.internal_id
        ]):
            logger.warning(f"No valid ID provided for title {media_data.series_title}")
            return

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
            f"tvdb: {media_data.tvdb_id}"
        )


async def add_media(media_data: MediaData) -> None:
    """
    Add media entry to database with localization.
    
    Args:
        media_data: Media data to add
        
    Raises:
        MediaServiceError: If addition fails
    """
    async with media_operation_context("add media"):
        logger.info(f"Processing media addition: {media_data}")
        
        # Get monitored seasons and localized title
        seasons = await _get_monitored_seasons(media_data)
        await _update_local_title(media_data)
        
        # Add to database
        add_to_db(media_data, seasons)
        
        logger.info(
            f"Added {media_data.series_title} with "
            f"tmdb: {media_data.tmdb_id}, "
            f"imdb: {media_data.imdb_id}, "
            f"tvdb: {media_data.tvdb_id}"
        )


async def _get_monitored_seasons(media_data: MediaData) -> List[int]:
    """Get monitored seasons for media."""
    if not media_data.internal_id:
        logger.warning("No internal ID provided for seasons lookup")
        return []
    return await sonarr.get_monitored_seasons(media_data.internal_id)


async def _update_local_title(media_data: MediaData) -> None:
    """Update media data with localized title."""
    if not media_data.tmdb_id:
        logger.warning("No TMDB ID provided for localization")
        return
        
    if local_title := await get_ukrainian_title(media_data.tmdb_id):
        media_data.local_title = local_title
    else:
        logger.warning(f"No Ukrainian title found for {media_data.series_title}")
