import logging

import httpx
from settings import SONARR_API_KEY, SONARR_URL


async def get_monitored_seasons(series_id: int):
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


async def tell_sonarr_manual_import(series_id, download_folder):
    url = f"{SONARR_URL}/api/v3/manualimport"

    headers = {
        "X-Api-Key": SONARR_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "name": "manualImport",
        "path": download_folder,
        "seriesId": series_id,
        "downloadClientId": "HOOK2STREAM",
        "approved": True,
        "files": []
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Sonarrr manualimport response for internal_id: {series_id}, Resp: {response.json()}")