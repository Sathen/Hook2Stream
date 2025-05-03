from enum import Enum
from typing import Optional, Dict
import httpx
from functools import lru_cache

from settings import TMDB_API_KEY
from logger import get_logger

logger = get_logger(__name__)

# Constants
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
CACHE_TTL: int = 3600  # Cache timeout in seconds


class MediaType(Enum):
    """Supported media types for TMDb API."""
    TV = "tv"
    MOVIE = "movie"


class TMDbClient:
    def __init__(self, api_key: str):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
    
    async def _make_request(self, endpoint: str) -> Optional[Dict]:
        url = f"{TMDB_BASE_URL}/{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"TMDb API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error when accessing TMDb API: {e}")
        
        return None

    # @lru_cache(maxsize=100, ttl=CACHE_TTL)
    async def get_ukrainian_title(
        self, 
        tmdb_id: int, 
        media_type: MediaType = MediaType.TV
    ) -> Optional[str]:
        endpoint = f"{media_type.value}/{tmdb_id}?language=uk-UA"
        data = await self._make_request(endpoint)
        
        if not data:
            return None
            
        # Movies use 'title', TV shows use 'name'
        return data.get("title") or data.get("name")


# Create singleton client instance
tmdb_client = TMDbClient(TMDB_API_KEY)

# Public API
async def get_ukrainian_title(
    tmdb_id: int, 
    media_type: str = "tv"
) -> Optional[str]:
    try:
        media_type_enum = MediaType(media_type)
    except ValueError:
        logger.error(f"Invalid media type: {media_type}")
        return None
        
    return await tmdb_client.get_ukrainian_title(tmdb_id, media_type_enum)
