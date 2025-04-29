from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MediaData(BaseModel):
    internal_id: Optional[int]
    date: str
    event_type: Optional[str]
    imdb_id: Optional[str]
    series_title: Optional[str]
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]
    local_title: Optional[str]


async def extract_fields(body_json) -> MediaData:
    event_type = body_json.get("eventType")
    series_title = None
    internal_id = None
    date = None
    tmdb_id = None
    imdb_id = None
    tvdb_id = None

    if "series" in body_json and isinstance(body_json["series"], dict):
        series_title = body_json["series"].get("title")
        date = body_json["series"].get("date", str(datetime.now()))
        tmdb_id = body_json["series"].get("tmdbId")
        internal_id = body_json["series"].get("id")
        imdb_id = body_json["series"].get("imdbId")
        tvdb_id = body_json["series"].get("tvdbId")

    return MediaData(
        internal_id=internal_id,
        date=date,
        event_type=event_type,
        imdb_id=imdb_id,
        series_title=series_title,
        tmdb_id=tmdb_id,
        tvdb_id=tvdb_id,
        local_title=None
    )
