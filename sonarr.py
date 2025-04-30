import os
from typing import List

import httpx

from models import MediaData
from settings import SONARR_API_KEY, SONARR_URL, RADARR_URL, RADARR_API_KEY, DOWNLOAD_DIR
from logger import get_logger

logger = get_logger(__name__)


async def get_monitored_seasons(series_id: int) -> List:
    url = f"{SONARR_URL}/api/v3/series/{series_id}"
    headers = {
        "X-Api-Key": SONARR_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    series_data = response.json()

    monitored_seasons = [
        season["seasonNumber"]
        for season in series_data.get("seasons", [])
        if season.get("monitored", False)
    ]

    return monitored_seasons


async def tell_sonarr_manual_import(media: MediaData, download_folder, season: int = 0):
    url = f"{SONARR_URL}/api/v3/manualimport"
    path = os.path.abspath(os.path.join(DOWNLOAD_DIR, download_folder))
    headers = {
        "X-Api-Key": SONARR_API_KEY,
        "Content-Type": "application/json"
    }

    payload = [
        {
            "path": path,
            "seriesId": media.internal_id,
            "seasonNumber": season,
            "languages": [
                {
                    "id": 1,
                    "name": "ukrainian"
                }
            ],
        }
    ]
    logger.info(f"[Sonarr Manual Import] payload: {payload}")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.info(f"[Sonarr Manual Import]  response for internal_id: {media.internal_id}, "
                     f"Response: {response.json()}")
        response.raise_for_status()


async def tell_radarr_manual_import(media: MediaData, download_folder: str):
    url = f"{RADARR_URL}/api/v3/manualimport"

    headers = {
        "X-Api-Key": RADARR_API_KEY,
        "Content-Type": "application/json"
    }

    payload = [
        {
            "path": download_folder,
            "movieId": media.internal_id,
            "movie": {
                "id": media.internal_id,
                "title": media.series_title,
                "tmdbId": media.tmdb_id,
                "path": download_folder,
                "monitored": True,
                "minimumAvailability": "released",
                "qualityProfileId": 1
            },
            "quality": {
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
            },
            "languages": [
                {
                    "id": 1,
                    "name": "ukrainian"
                }
            ]
        }
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.info(f"[Radarr Manual Import] response for internal_id: {media.internal_id}, "
                     f"Resp: {response.json()}")
        response.raise_for_status()
