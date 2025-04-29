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
