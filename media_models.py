from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel


class Episode(BaseModel):
    episode_number: int
    name: str
    overview: str
    air_date: str
    still_path: Optional[str] = None
    embed_url: Optional[str] = None

    @staticmethod
    def from_json(data: dict, embed_url: Optional[str] = None) -> "Episode":
        return Episode(
            episode_number=data["episode_number"],
            name=data["name"],
            overview=data["overview"],
            air_date=data["air_date"],
            still_path=data.get("still_path"),
            embed_url=embed_url,
        )


class SearchStreamItem(BaseModel):
    title: str
    year: int
    season: Optional[int]
    number_of_episodes: Optional[int]
    url: str


class StreamsSearchRequest(BaseModel):
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    season_number: Optional[int] = None
    media_type: str
    episode_number: Optional[int] = None
    total_episodes: Optional[int] = None

    @staticmethod
    def from_json(data: dict) -> "StreamsSearchRequest":
        return StreamsSearchRequest(title=data.get("title"),
                                    original_title=data.get("original_title"),
                                    year=data.get("year"),
                                    season_number=data.get("season_number"),
                                    episode_number=data.get("episode_number"),
                                    media_type=data.get("media_type"),
                                    )


class Season(BaseModel):
    seasonNumber: int
    url: str
    name: str
    overview: str
    poster_path: Optional[str] = None
    air_date: Optional[str]
    numberOfEpisodes: int
    embed_episodes_urls: dict[int, str]
    episodes: list[Episode]

    @staticmethod
    def from_json(season_data: dict, url: str, embed_episodes_urls: dict[int, str]) -> "Season":
        episodes = [
            Episode.from_json(ep, embed_url=embed_episodes_urls.get(ep["episode_number"]))
            for ep in season_data.get("episodes", [])
        ]

        return Season(
            seasonNumber=season_data.get("season_number"),
            url=url,
            name=season_data.get("name", ''),
            overview=season_data.get("overview", ''),
            poster_path=season_data.get("poster_path"),
            air_date=season_data.get("air_date", ''),
            numberOfEpisodes=len(episodes),
            embed_episodes_urls=embed_episodes_urls,
            episodes=episodes,
        )


class LinkTranslator(BaseModel):
    quality: str
    url: str


class Translator(BaseModel):
    name: str
    links: List[LinkTranslator]

class Translators(BaseModel):
    source_name:str
    sources: List[Translator]

class TranslatorData(BaseModel):
    data: List[Translators]


@dataclass
class MediaDTO:
    tmdb_id: int
    title: str
    description: str
    cast: List[str]
    year: str
    rating: float
    posterPath: str
    backdropPath: str

    def __init__(self):
        pass


@dataclass
class MovieDTO(MediaDTO):
    embed_url: str
    pass


@dataclass
class TvSeriesDTO(MediaDTO):
    seasons: List[Season]


class MediaData(BaseModel):
    internal_id: int
    created_on: str
    source_type: str
    event_type: Optional[str]
    imdb_id: Optional[str]
    series_title: Optional[str]
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]
    local_title: Optional[str]


class SearchItem(BaseModel):
    title: str
    path: str
    img: str
    year: Optional[int]
    rating: Optional[float]


class SearchResult(BaseModel):
    items: list[SearchItem]


class Media(BaseModel):
    title: str
