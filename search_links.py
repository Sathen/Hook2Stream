import json
import time
from typing import List, Optional, Dict, Any
import urllib.parse
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag
from ratelimit import limits, sleep_and_retry

from models import MediaData
from settings import USER_AGENT, HOST, SEARCH_QUERY
from logger import get_logger

logger = get_logger(__name__)

# Constants
CALLS_PER_MINUTE = 30
REQUEST_TIMEOUT = 10
DELAY_BETWEEN_REQUESTS = 1

class VideoSearchError(Exception):
    """Base exception for video search errors."""
    pass

class ParseError(VideoSearchError):
    """Raised when parsing fails."""
    pass

class NetworkError(VideoSearchError):
    """Raised when network requests fail."""
    pass

@dataclass
class FilmData:
    """Structure for film metadata."""
    type: str
    url: str
    seasons: Optional[List[Dict[str, Any]]] = None

class VideoSearchClient:
    """Handles video search and link extraction."""
    
    def __init__(self, user_agent: str = USER_AGENT):
        self.headers = {"User-Agent": user_agent}
    
    @sleep_and_retry
    @limits(calls=CALLS_PER_MINUTE, period=60)
    def _get_document(self, url: str) -> BeautifulSoup:
        """Fetch and parse webpage with rate limiting."""
        try:
            response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            raise NetworkError(f"Failed to fetch {url}: {str(e)}")

    def search_film(self, media: MediaData, season: Optional[int] = None) -> List[str]:
        logger.info(f"Searching for: {media.series_title}")
        links: List[str] = []
        
        # Try both local and original titles
        link_to_film = self._find_film_link(media, season)
        if not link_to_film:
            logger.info("Film not found")
            return []

        film_data = self._get_film_data(HOST + link_to_film["href"])
        embed_urls = self._get_embed_urls(film_data, season)

        for url in embed_urls:
            time.sleep(DELAY_BETWEEN_REQUESTS)
            if source_url := self._extract_video_source(url):
                links.append(source_url)

        return links

    def _find_film_link(self, media: MediaData, season: Optional[int]) -> Optional[Tag]:
        """Find the film link trying different title variants."""
        for title in [media.local_title, media.series_title]:
            if link := self._try_get_link_to_film(title, season):
                return link
        return None

    def _try_get_link_to_film(self, title: str, season: Optional[int]) -> Optional[Tag]:
        """Try to find film link for given title."""
        search_url = self._build_search_url(title, season)
        search_doc = self._get_document(search_url)
        return search_doc.select_one("div#block-search-page div.row div.col div.item a[href]")

    def _extract_video_source(self, url: str) -> Optional[str]:
        """Extract video source URL from embed page."""
        try:
            embed_doc = self._get_document(url)
            video_options = embed_doc.select("option[data-type=link]")
            return self._get_best_quality_url(video_options)
        except (NetworkError, ParseError):
            logger.error(f"Failed to extract video source from {url}")
            return None

    @staticmethod
    def _get_best_quality_url(video_options: List[Tag]) -> Optional[str]:
        """Get highest quality video URL."""
        for option in video_options:
            value = option.get("value", "")
            if "ashdi" in value:  # HD quality
                return value
        return None if not video_options else video_options[0].get("value")

    def _get_film_data(self, url: str) -> FilmData:
        """Extract film metadata from page."""
        film_page = self._get_document(url)
        script_tag = film_page.find('script', type='application/ld+json')
        
        if not script_tag or not script_tag.string:
            raise ParseError("Missing film metadata")
            
        try:
            data = json.loads(script_tag.string)
            return FilmData(
                type=data['@type'],
                url=data['url'],
                seasons=data.get('containsSeason')
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ParseError(f"Invalid film metadata: {str(e)}")

    def _get_embed_urls(self, film_data: FilmData, season: Optional[int]) -> List[str]:
        """Get embed URLs based on media type."""
        if film_data.type == 'TVSeason':
            return self._get_tv_embed_urls(film_data, season)
        return [self._get_movie_embed_url(film_data)]

    def _get_movie_embed_url(self, film_data: FilmData) -> str:
        """Get embed URL for movies."""
        film_doc = self._get_document(film_data.url)
        embed_iframe = film_doc.select_one("div.video-holder iframe#embed")
        if not embed_iframe or "src" not in embed_iframe.attrs:
            raise ParseError("Movie embed URL not found")
        return HOST + embed_iframe["src"]

    def _get_tv_embed_urls(self, film_data: FilmData, season: Optional[int]) -> List[str]:
        """Get embed URLs for TV shows."""
        season_index = (season or 1) - 1
        season_url = film_data.seasons[season_index]['url']
        film_doc = self._get_document(season_url)
        
        options = film_doc.select("select#select-series option[data-series-number]")
        return [HOST + option["value"] for option in options if "value" in option.attrs]

    @staticmethod
    def _build_search_url(title: str, season: Optional[int]) -> str:
        """Build search URL with parameters."""
        search_value = f"{title} {season}" if season else title
        normalized_title = urllib.parse.quote_plus(search_value)
        return f"{HOST}/{SEARCH_QUERY}{normalized_title}"

# Create singleton instance
video_search = VideoSearchClient()

# Public API
def search_film(media: MediaData, season: Optional[int] = None) -> List[str]:
    """Public interface for video search."""
    return video_search.search_film(media, season)
