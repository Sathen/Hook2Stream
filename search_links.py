import asyncio
import json
import re
import urllib.parse
from enum import Enum
from typing import Any, Optional, List, Dict, Union

import cloudscraper
from bs4 import BeautifulSoup
from fastapi.openapi.models import MediaType

from logger import get_logger
from media_models import MediaData, SearchStreamItem
from settings import HOST, SEARCH_QUERY

logger = get_logger(__name__)

scrapper = cloudscraper.create_scraper()

class MediaType(Enum):
    TV = "tv",
    MOVIE = "movie"


def get_document(url: str) -> BeautifulSoup:
    response = scrapper.get(url, timeout=10)
    if response.status_code != 200:
        return BeautifulSoup("", "html.parser")
    return BeautifulSoup(response.text, "html.parser")


async def get_document_async(url: str) -> BeautifulSoup:
    return await asyncio.to_thread(get_document, url)

def search_film(media: MediaData, season: int = None):
    links = []
    title_candidates = [media.local_title, media.series_title]

    for title in title_candidates:
        link_to_film = try_get_link_to_film(title, season)
        if link_to_film:
            break
    else:
        logger.info("Film was not found.")
        return []

    film_page_url = HOST + link_to_film["href"]
    film_data = get_film_data(film_page_url)
    embed_urls = get_embed_url(film_data, season).values()

    for url in embed_urls:
        embed_doc = get_document(url)
        if not embed_doc:
            logger.info(f"Embed link not found: {url}")
            return []
        video_options = embed_doc.select("option[data-type=link]")
        links.append(get_source_url(video_options))

    return links


def try_get_link_to_film(title, season: int = None, search_type: Optional[str] = None):
    search_url = get_search_url(title, season, search_type)
    search_doc = get_document(search_url)

    if season:
        return search_doc.select_one(
            f"div#block-search-page div.row div.col div.item a[href]"
        )
    else:
        return search_doc.select_one(f"div#block-search-page div.row div.col div.item a[href]")


async def find_by_title_all(title: str, search_type: str) -> List[SearchStreamItem]:
    if not title:
        return []

    search_url = new_get_search_url(title, MediaType[search_type.upper()])
    search_doc = await get_document_async(search_url)
    raw_search_items = search_doc.select("div#block-search-page div.row div.col div.item")
    search_items = []
    for item in raw_search_items:
        title = item.select_one("div.item__data div.name")["title"].strip()
        url = item.select_one("div.item__data a.w--100")["href"].strip()
        year = item.select_one("div.item__data div.info a.info__item").text.strip()
        season = None
        episodes_num = None
        if item.select_one("div.last-episode"):
            raw_episode_text = item.select_one("div.last-episode").text
            parsed = _parse_season_episode(raw_episode_text)
            season = parsed.get("season")
            episodes_num = parsed.get("number_of_episodes")

        result = SearchStreamItem(title=title, url=url, year=year, season=season, number_of_episodes=episodes_num)
        search_items.append(result)

    return search_items


def _parse_season_episode(text: Optional[str] = None) -> Optional[dict[str, int]]:
    if not text:
        return {}

    text = text.strip().lower()

    pattern = r'(\d+)\s*сезон\s*(\d+)\s*серія'

    match = re.search(pattern, text)

    if match:
        season_num = int(match.group(1))
        episode_num = int(match.group(2))

        return {
            'season': season_num,
            'number_of_episodes': episode_num
        }
    else:
        return {}


def get_source_url(video_options):
    for option in video_options:
        value = option.get("value", "")
        if "ashdi" in value:
            return value


async def get_movie_embed_url_async(film_data: Any) -> Optional[str]:
    try:
        film_page_url = film_data["url"]
        film_doc = await get_document_async(film_page_url)
        embed_iframe = film_doc.select_one("div.video-holder iframe#embed")
        return HOST + embed_iframe["src"]
    except Exception as e:
        logger.error(f"Error getting movie embed URL: {e}")
        return None


async def get_embed_url(film_data: Any, season: int) -> Optional[Union[Dict[int, str], Dict[str, str]]]:
    content_type = film_data.get("@type")
    if not content_type:
        logger.warning("No @type found in film_data")
        return None

    try:
        if content_type == "TVSeason":
            return await get_tv_embed_url(film_data, season)
        elif content_type == "Movie":
            movie_url = await get_movie_embed_url_async(film_data)
            return {1: movie_url} if movie_url else None
        else:
            logger.info(f"Unsupported content type: {content_type}")
            return None
    except Exception as e:
        logger.error(f"Error in get_embed_url: {e}")
        return None


async def get_tv_embed_url(film_data: Any, season: int) -> Dict[int, str]:
    try:
        seasons = film_data.get("partOfTVSeries", {}).get("containsSeason", [])

        season_index = max(0, season - 1)

        if season_index >= len(seasons):
            logger.warning(f"Season {season} not found, only {len(seasons)} seasons available")
            return {}

        season_data = seasons[season_index]
        if not season_data.get("url"):
            logger.warning(f"No URL found for season {season}")
            return {}

        return await get_tv_embed_urls(season_data["url"])
    except Exception as e:
        logger.error(f"Error getting TV embed URL for season {season}: {e}")
        return {}


async def get_tv_embed_urls(url: str) -> Dict[int, str]:
    """Async version that properly handles document fetching."""
    try:
        film_doc = await get_document_async(url)
        embed_options = film_doc.select("select#select-series option[data-series-number]")

        result = {}
        for option in embed_options:
            if option.get("data-series-number") and option.get("value"):
                series_number = option["data-series-number"]
                url = HOST + option["value"]

                if "-" in series_number:
                    # Handle range like "10-11"
                    start, end = map(int, series_number.split("-"))
                    for num in range(start, end + 1):
                        result[num] = url
                else:
                    # Handle single number
                    result[int(series_number)] = url

        return result
    except Exception as e:
        logger.error(f"Error getting TV embed URLs from {url}: {e}")
        return {}


def get_search_url(film_name_r: str, season: int = None, search_type: Optional[str] = None):
    search_value = film_name_r
    if season and not film_name_r.isascii():
        search_value = film_name_r + " " + str(season)

    normalize_params = urllib.parse.quote_plus(search_value)
    search_url = f"{HOST}/{SEARCH_QUERY}{normalize_params}&type={search_type}"
    return search_url


def new_get_search_url(title: str, search_type: MediaType = MediaType.TV) -> str:
    search_value = title
    normalize_params = urllib.parse.quote_plus(search_value)
    normalize_params = normalize_params.replace('.', ':')
    search_url = f"{HOST}/{SEARCH_QUERY}{normalize_params}&type={search_type.value[0]}"
    return search_url


def fix_description_field(text):
    pattern = r'"description":\s*"(.+?)"(,?\s*\n\s*"url")'  # Match everything until the next field
    match = re.search(pattern, text, re.DOTALL)
    if match:
        raw_description = match.group(1)
        # Escape internal newlines and strip leading/trailing spaces
        escaped = raw_description.replace('\n', '\\n').replace('\r', '').strip()
        fixed_block = f'"description": "{escaped}"{match.group(2)}'
        return text[:match.start()] + fixed_block + text[match.end():]
    return text


async def get_film_data(url: str) -> Dict[Any, Any]:
    try:
        film_page = await get_document_async(url)
        script_tag = film_page.find("script", type="application/ld+json")

        json_data = script_tag.string.strip()
        try:
            cleaned_json_data = fix_description_field(json_data)
            response = json.loads(cleaned_json_data)
            response['original_name'] = film_page.select_one("div.original").text.strip()
            return response
        except json.JSONDecodeError:
            try:
                import demjson3
                response = demjson3.decode(cleaned_json_data)
                response['original_name'] = film_page.select_one("div.original").text.strip()
                return response
            except Exception as e:
                logger.error(f"JSON parsing failed for {url}: {e}")
                return {}

    except Exception as e:
        logger.error(f"Error getting film data from {url}: {e}")
        return {}
