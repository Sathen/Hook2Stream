import httpx
from typing import Optional
from settings import TMDB_API_KEY
from logger import get_logger

logger = get_logger(__name__)

TMDB_BASE_URL: str = "https://api.themoviedb.org/3"


async def get_ukrainian_title(tmdb_id: int, media_type: str = "tv") -> Optional[str]:
    """
    Отримати українську назву серіалу або фільму за TMDb ID.

    :param tmdb_id: TMDb ID фільму або серіалу
    :param media_type: 'tv' або 'movie'
    :return: Назва українською мовою або None
    """
    url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}?language=uk-UA"
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "Accept": "application/json"
    }

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
