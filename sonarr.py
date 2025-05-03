from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

import httpx
from httpx import Response

from models import MediaData
from settings import (
    SONARR_API_KEY, 
    SONARR_URL, 
    RADARR_URL, 
    RADARR_API_KEY, 
    DOWNLOAD_DIR
)
from logger import get_logger

logger = get_logger(__name__)

# Constants
UKRAINIAN_LANGUAGE = {"id": 1, "name": "ukrainian"}
DEFAULT_QUALITY_PROFILE = {
    "quality": {
        "id": 1,
        "name": "HD-720p",
        "source": "web",
        "resolution": 720,
        "modifier": "none"
    },
    "revision": {
        "version": 1,
        "real": 0,
        "isRepack": True
    }
}

class MediaClientError(Exception):
    """Base exception for media client errors."""
    pass

class ServiceType(Enum):
    """Supported media services."""
    SONARR = "sonarr"
    RADARR = "radarr"

@dataclass
class ServiceConfig:
    """Configuration for media service."""
    url: str
    api_key: str

class MediaClientBase:
    """Base class for media service clients."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.headers = {
            "X-Api-Key": config.api_key,
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Response:
        """Make HTTP request to service API."""
        url = f"{self.config.url}/api/v3/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method, 
                    url, 
                    headers=self.headers, 
                    **kwargs
                )
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                logger.error(f"API request failed: {str(e)}")
                raise MediaClientError(f"API request failed: {str(e)}")

class SonarrClient(MediaClientBase):
    """Client for Sonarr API interactions."""
    
    async def get_monitored_seasons(self, series_id: int) -> List[int]:
        """Get list of monitored season numbers."""
        response = await self._make_request("GET", f"series/{series_id}")
        series_data = response.json()
        
        return [
            season["seasonNumber"]
            for season in series_data.get("seasons", [])
            if season.get("monitored", False)
        ]
    
    async def manual_import(
        self, 
        media: MediaData, 
        download_folder: Path, 
        season: int = 0
    ) -> None:
        """Trigger manual import in Sonarr."""
        payload = [{
            "path": str(download_folder.absolute()),
            "seriesId": media.internal_id,
            "seasonNumber": season,
            "languages": [UKRAINIAN_LANGUAGE]
        }]
        
        logger.info(f"[Sonarr] Manual import payload: {payload}")
        response = await self._make_request("POST", "manualimport", json=payload)
        logger.info(f"[Sonarr] Manual import response: {response.json()}")

class RadarrClient(MediaClientBase):
    """Client for Radarr API interactions."""
    
    async def manual_import(self, media: MediaData, download_folder: Path) -> None:
        """Trigger manual import in Radarr."""
        payload = [{
            "path": str(download_folder),
            "movieId": media.internal_id,
            "movie": {
                "id": media.internal_id,
                "title": media.series_title,
                "tmdbId": media.tmdb_id,
                "path": str(download_folder),
                "monitored": True,
                "minimumAvailability": "released",
                "qualityProfileId": 1
            },
            "quality": DEFAULT_QUALITY_PROFILE,
            "languages": [UKRAINIAN_LANGUAGE]
        }]
        
        logger.info(f"[Radarr] Manual import payload: {payload}")
        response = await self._make_request("POST", "manualimport", json=payload)
        logger.info(f"[Radarr] Manual import response: {response.json()}")

# Create client instances
sonarr_client = SonarrClient(ServiceConfig(SONARR_URL, SONARR_API_KEY))
radarr_client = RadarrClient(ServiceConfig(RADARR_URL, RADARR_API_KEY))

# Public API
async def get_monitored_seasons(series_id: int) -> List[int]:
    """Get monitored seasons for a series."""
    return await sonarr_client.get_monitored_seasons(series_id)

async def tell_sonarr_manual_import(
    media: MediaData, 
    download_folder: str, 
    season: int = 0
) -> None:
    """Trigger Sonarr manual import."""
    path = Path(DOWNLOAD_DIR) / download_folder
    await sonarr_client.manual_import(media, path, season)

async def tell_radarr_manual_import(media: MediaData, download_folder: str) -> None:
    """Trigger Radarr manual import."""
    path = Path(DOWNLOAD_DIR) / download_folder
    await radarr_client.manual_import(media, path)
