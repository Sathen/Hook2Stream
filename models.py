from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class MediaSourceType(Enum):
    """Media source types."""
    SONARR = "SONARR"
    RADARR = "RADARR"


class MediaEventType(Enum):
    """Media event types."""
    GRABBED = "Grabbed"
    IMPORTED = "Import"
    DELETED = "Deleted"


class MediaData(BaseModel):
    """
    Media data model with validation.
    
    Attributes:
        internal_id: Internal ID from Sonarr/Radarr
        created_on: Timestamp of creation
        source_type: Source system (SONARR/RADARR)
        event_type: Event type that triggered the webhook
        imdb_id: IMDB ID if available
        series_title: Title of series/movie
        tmdb_id: TMDB ID if available
        tvdb_id: TVDB ID if available
        local_title: Localized title if available
    """
    internal_id: int = Field(..., description="Internal ID from media system")
    created_on: str = Field(..., description="Creation timestamp")
    source_type: str = Field(..., description="Source system type")
    event_type: Optional[str] = Field(None, description="Event type")
    imdb_id: Optional[str] = Field(None, description="IMDB ID")
    series_title: Optional[str] = Field(None, description="Media title")
    tmdb_id: Optional[int] = Field(None, description="TMDB ID")
    tvdb_id: Optional[int] = Field(None, description="TVDB ID")
    local_title: Optional[str] = Field(None, description="Localized title")

    class Config:
        """Pydantic model configuration."""
        allow_population_by_field_name = True
        validate_assignment = True


class MediaMapper:
    """Base class for mapping webhook responses to MediaData."""
    
    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    @staticmethod
    def extract_common_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract common fields from response data."""
        return {
            "event_type": data.get("eventType"),
            "created_on": MediaMapper.get_current_timestamp()
        }


class SonarrMapper(MediaMapper):
    """Mapper for Sonarr webhook responses."""
    
    @classmethod
    async def map_response(cls, body_json: Dict[str, Any]) -> MediaData:
        """Map Sonarr webhook response to MediaData."""
        common_fields = cls.extract_common_fields(body_json)
        series_data = body_json.get("series", {})
        
        if not isinstance(series_data, dict):
            series_data = {}
            
        return MediaData(
            internal_id=series_data.get("id"),
            series_title=series_data.get("title"),
            tmdb_id=series_data.get("tmdbId"),
            imdb_id=series_data.get("imdbId"),
            tvdb_id=series_data.get("tvdbId"),
            source_type=MediaSourceType.SONARR.value,
            local_title=None,
            **common_fields
        )


class RadarrMapper(MediaMapper):
    """Mapper for Radarr webhook responses."""
    
    @classmethod
    async def map_response(cls, body_json: Dict[str, Any]) -> MediaData:
        """Map Radarr webhook response to MediaData."""
        common_fields = cls.extract_common_fields(body_json)
        movie_data = body_json.get("movie", {})
        
        if not isinstance(movie_data, dict):
            movie_data = {}
            
        return MediaData(
            internal_id=movie_data.get("id"),
            series_title=movie_data.get("title"),
            tmdb_id=movie_data.get("tmdbId"),
            imdb_id=movie_data.get("imdbId"),
            tvdb_id=None,
            source_type=MediaSourceType.RADARR.value,
            local_title=None,
            **common_fields
        )


# Public API
async def map_sonarr_response(body_json: Dict[str, Any]) -> MediaData:
    """Map Sonarr webhook response to MediaData."""
    return await SonarrMapper.map_response(body_json)


async def map_radarr_response(body_json: Dict[str, Any]) -> MediaData:
    """Map Radarr webhook response to MediaData."""
    return await RadarrMapper.map_response(body_json)
