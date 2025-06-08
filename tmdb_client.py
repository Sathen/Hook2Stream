import httpx
from typing import Optional, Any, List, Dict
from settings import TMDB_API_KEY
from logger import get_logger
import requests

logger = get_logger(__name__)

TMDB_BASE_URL: str = "https://api.themoviedb.org/3"


async def get_ukrainian_title(tmdb_id: int, media_type: str = "tv") -> Optional[str]:
    url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}?language=uk-UA"
    headers = {"Authorization": f"Bearer {TMDB_API_KEY}", "Accept": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            return data.get("title") or data.get("name")

    except httpx.HTTPStatusError as e:
        logger.error(f"TMDb API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error when accessing TMDb API: {e}")

    return None


async def get_tmdb_details(tmdb_id: int, media_type: str = "tv") -> dict[str, Any]:
    url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}?language=uk-UA"
    headers = {"Authorization": f"Bearer {TMDB_API_KEY}", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data

    except httpx.HTTPStatusError as e:
        logger.error(f"TMDb API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error when accessing TMDb API: {e}")

    return None


async def get_tmdb_season(tmdb_id: int, season_number: int) -> dict[str, Any]:
    url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/season/{season_number}?language=uk-UA"
    headers = {"Authorization": f"Bearer {TMDB_API_KEY}", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data

    except httpx.HTTPStatusError as e:
        logger.error(f"TMDb API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error when accessing TMDb API: {e}")

    return None


def _adopt_search_param(name) -> List[str]:
    name = (name
     .replace("?", "")
     .replace("&", "")
     .replace("'", "")
     .replace('"', ""))
    if '[' in name:
        return [name[:name.index('[')].strip(), name[name.index('[')+1:name.rindex(']')-1].strip()]
    if '/' in name:
        return [name[:name.index('/')].strip(), name[name.index('/')+1:].strip()]
    return [name.strip()]


async def search_by_name(names: List[str], year:Optional[Any], media_type: str = "tv") -> Dict[str, Optional[Any]]:
    search_names = []
    for name in names:
        search_names.extend(_adopt_search_param(name))

    url = f"{TMDB_BASE_URL}/search/{media_type}"

    params = []
    for name in search_names:
        params.append({
            "query": name,
            "year": year,
            "language": "uk-UA",
        })

    headers = {"Authorization": f"Bearer {TMDB_API_KEY}", "Accept": "application/json"}

    try:
        for param in params:
            response = requests.get(url, params=param, headers=headers)
            data = response.json()
            if data.get("results", []) is None or len(data.get("results", [])) == 0:
                continue
            return data.get("results", [])[0]
        return {}

    except httpx.HTTPStatusError as e:
        logger.error(f"TMDb API error: {e.response.status_code} - {e.response.text}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error when accessing TMDb API: {e}")
        return {}
