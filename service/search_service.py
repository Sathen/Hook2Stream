import json
import re
import time
from typing import Any, List

import demjson3

import tmdb_client
from download import get_direct_stream_urls
from logger import get_logger
from media_models import MediaDTO, SearchItem, SearchResult, TranslatorData, Translator, StreamsSearchRequest, \
    LinkTranslator, Translators
from media_models_factory import get_movie_data, get_tv_data
from search_links import get_document, get_film_data, get_search_url, get_embed_url, \
    find_by_title_all, get_document_async
from search_stream_matcher import find_best_match
from settings import HOST

constants = {
    "select_all_items": "div#block-search-page div.row div.col div.item",
    "select_desc": "a[href][title]:not([class]):not([id])",
    "select_img": "img[src]",
    "select_rating": "div[data-mark]",
}

excluded_sources = {"videocdn", "voidboost", "vidsrc"}

logger = get_logger(__name__)


def search(name: str) -> SearchResult:
    url = get_search_url(name)
    logger.info(f"Search URL: {url}")
    search_doc = get_document(url)
    search_items = search_doc.select(constants["select_all_items"])

    items: list[Any] = []

    for result in search_items:
        desc = result.select_one(constants["select_desc"])
        title = str(desc["title"])
        rating = result.select_one(constants["select_rating"]).get("data-mark")
        link = _construct_full_url(str(desc["href"]))
        img = _construct_full_url(result.select_one(constants["select_img"]).get("src"))

        item = SearchItem(title=title, path=link, img=img, year=0, rating=rating)
        items.append(item)

    logger.info(f"Found {len(items)} items.")
    return SearchResult(items=items)


async def get_videos(embed_path: str) -> TranslatorData:
    if not embed_path:
        logger.warning("Embed path is empty.")
        return TranslatorData(data=[])

    embed_doc = await get_document_async(embed_path)
    serial_data = _extract_serial_data(embed_doc)

    start_time = time.time()
    translators = _extract_episode_links(serial_data)
    time_elapsed = time.time() - start_time
    logger.info(f"Found {len(translators)} translators. with {time_elapsed} seconds.")
    return TranslatorData(data=translators)


from concurrent.futures import ThreadPoolExecutor, as_completed


def _extract_episode_links(serial_data) -> List[Translators]:
    episode_number = serial_data["episode"]

    # Check if it's a movie (list structure) or TV show (dict structure)
    # For movies, get all episodes; for TV shows, get specific episode
    first_episode_src = serial_data["episodes"][0]["src"]

    if isinstance(first_episode_src, list):
        filtered_episodes = [
            episode for episode in serial_data["episodes"]
            if all(ex_src not in episode["title"].lower() for ex_src in excluded_sources)
        ]

        source_items = []
        for episode in filtered_episodes:
            source_name = episode["title"].replace("Серія ", "").strip()
            source_items.append((source_name, episode["src"]))

        filtered_sources = filtered_episodes
    else:
        # TV show: process specific episode
        episode_index = episode_number - 1
        episode_sources = serial_data["episodes"][episode_index]["src"]

        # Pre-filter excluded sources for TV shows
        filtered_sources = {k: v for k, v in episode_sources.items() if k not in excluded_sources}
        source_items = filtered_sources.items()

    if not filtered_sources:
        return []

    translators_list = []

    # Calculate max_workers based on actual structure
    if isinstance(first_episode_src, list):
        total_links = sum(len(episode["src"]) for episode in filtered_sources)
    else:
        total_links = sum(len(links) for links in filtered_sources.values())

    max_workers = min(32, total_links * 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_data = {}

        for source_key, source_links in source_items:
            for link_data in source_links:
                future = executor.submit(_extract_video_links, link_data["link"], source_key)
                future_to_data[future] = (source_key, link_data)

        # Group results by source
        source_results = {}
        for future in as_completed(future_to_data):
            source_key, link_data = future_to_data[future]
            try:
                links = future.result()
                translator = Translator(name=link_data["name"], links=links)

                if source_key not in source_results:
                    source_results[source_key] = []
                source_results[source_key].append(translator)

            except Exception as e:
                print(f"Error processing {source_key} link {link_data['link']}: {e}")

        # Build final list
        if isinstance(first_episode_src, list):
            # Movie: create Translators for each source (by title)
            for source_name in set(source_key for source_key, _ in source_items):
                if source_name in source_results:
                    translators_list.append(Translators(
                        source_name=source_name,
                        sources=source_results[source_name]
                    ))
        else:
            # TV show: iterate through filtered source keys
            for source_key in filtered_sources.keys():
                if source_key in source_results:
                    translators_list.append(Translators(
                        source_name=source_key,
                        sources=source_results[source_key]
                    ))

    return translators_list


def _extract_serial_data(soup):
    # Find all script tags
    script_tags = soup.find_all('script')

    for script in script_tags:
        script_content = script.string
        if script_content and 'window.SERIAL_DATA' in script_content:
            pattern = r'window\.SERIAL_DATA\s*=\s*({.*?})\s*(?:;|\n|$)'
            match = re.search(pattern, script_content, re.DOTALL)

            if match:
                json_str = match.group(1)
                try:
                    return demjson3.decode(json_str)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    return None

    return None


async def get_media(path: str) -> MediaDTO:
    film_data = await get_film_data(path)
    original_name = str(film_data["original_name"])
    if film_data["@type"] == "Movie":
        names = [original_name, str(film_data["name"])]
        tmdb_data = await tmdb_client.search_by_name(names, media_type="movie")
        return await get_movie_data(film_data, tmdb_data)
    elif film_data["@type"] in ["TVSeries", "TVSeason"]:
        film_data = film_data["partOfTVSeries"]
        series_names = [original_name, str(film_data["name"])]
        tmdb_data = await tmdb_client.search_by_name(series_names, media_type="tv")
        tmdb_data = await tmdb_client.get_tmdb_details(tmdb_data["id"], media_type="tv")
        return await get_tv_data(film_data, tmdb_data)

    return MediaDTO()


def _extract_video_links(link: str, source: str) -> List[LinkTranslator]:
    # if link.__contains__("vidsrc"):
    #     return []
    if source == "spilberg":
        resp = get_document(link)
        matches = re.findall(r'https?://[^\s"\'<>]+\.m3u8?', str(resp))
        if len(matches) == 0:
            return []
        return get_direct_stream_urls(matches[0])

    return get_direct_stream_urls(link)


def _construct_full_url(name: str) -> str:
    return f"{HOST}{name}"


async def new_get_film_streams(search_request: StreamsSearchRequest):
    all_results = []
    # Search by title
    start_time = time.time()
    title_results = await find_by_title_all(search_request.title, search_type=search_request.media_type)
    stop_time = time.time() - start_time
    logger.info(f"Found {len(title_results)} for time: {stop_time}")
    if title_results:
        all_results.extend(title_results)

    # Search by original_title if available
    if search_request.original_title and len(title_results) == 0:
        original_results = await find_by_title_all(search_request.original_title, search_type=search_request.media_type)
        if original_results:
            all_results.extend(original_results)

    # Remove duplicates (by URL or title+year combination)
    unique_results = []
    seen_urls = set()
    for item in all_results:
        if item.url not in seen_urls:
            unique_results.append(item)
            seen_urls.add(item.url)

    # Find the best match
    best_match = find_best_match(search_request, unique_results)
    if not best_match:
        logger.info("Not found best match.")
        return []

    film_page_url = HOST + best_match.url
    film_data = await get_film_data(film_page_url)
    urls = await get_embed_url(film_data, search_request.season_number)

    if search_request.episode_number is not None:
        embed_url = urls.get(search_request.episode_number)
    else:
        embed_url = urls[1]

    return await get_videos(embed_url)
