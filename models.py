from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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


async def map_sonarr_response(body_json) -> MediaData:
    event_type = body_json.get("eventType")
    series_title = None
    internal_id = None
    created_on = None
    tmdb_id = None
    imdb_id = None
    tvdb_id = None

    if "series" in body_json and isinstance(body_json["series"], dict):
        series_title = body_json["series"].get("title")
        created_on = str(datetime.now())
        tmdb_id = body_json["series"].get("tmdbId")
        internal_id = body_json["series"].get("id")
        imdb_id = body_json["series"].get("imdbId")
        tvdb_id = body_json["series"].get("tvdbId")

    return MediaData(
        internal_id=internal_id,
        created_on=created_on,
        source_type="SONARR",
        event_type=event_type,
        imdb_id=imdb_id,
        series_title=series_title,
        tmdb_id=tmdb_id,
        tvdb_id=tvdb_id,
        local_title=None
    )


async def map_radarr_response(body_json) -> MediaData:
    event_type = body_json.get("eventType")
    series_title = None
    internal_id = None
    created_on = None
    tmdb_id = None
    imdb_id = None
    tvdb_id = None
    local_title = None

    movie = body_json.get("movie", {})

    if isinstance(movie, dict):
        series_title = movie.get("title")
        created_on = str(datetime.now())
        tmdb_id = movie.get("tmdbId")
        internal_id = movie.get("id")
        imdb_id = movie.get("imdbId")

    return MediaData(
        internal_id=internal_id,
        created_on=created_on,
        source_type="RADARR",
        event_type=event_type,
        imdb_id=imdb_id,
        series_title=series_title,
        tmdb_id=tmdb_id,
        tvdb_id=tvdb_id,
        local_title=local_title
    )
