from datetime import datetime
from typing import Any

import tmdb_client
from media_models import MediaData, MovieDTO, Season, TvSeriesDTO
from search_links import get_movie_embed_url_async, get_tv_embed_urls
from settings import IMG_HOST


async def get_movie_data(film_data: Any, tmdb_data: Any) -> MovieDTO:
    title = film_data["name"]
    poster_path = IMG_HOST + tmdb_data.get("poster_path")
    backdrop_path = IMG_HOST + tmdb_data.get("backdrop_path")
    rating = tmdb_data.get("vote_average")
    year = tmdb_data.get("first_air_date") or tmdb_data.get("release_date")
    cast = [actor.get("name") for actor in film_data.get("actor", [])]
    description = film_data.get("description")
    embed_url = await get_movie_embed_url_async(film_data)
    return MovieDTO(
        tmdb_id=tmdb_data["id"],
        title=title,
        description=description,
        cast=cast,
        year=year,
        rating=rating,
        posterPath=poster_path,
        backdropPath=backdrop_path,
        embed_url=embed_url,
    )


async def get_tv_data(film_data: Any, tmdb_data: Any) -> TvSeriesDTO:
    tmdb_id = tmdb_data["id"]
    seasons_data = film_data.get("containsSeason", [])

    seasons = []
    for season in seasons_data:
        season_number = season.get("seasonNumber")
        season_url = season.get("url")
        embed_episode_urls = await get_tv_embed_urls(season_url)  # {episode_number: embed_url}

        season_details = await tmdb_client.get_tmdb_season(tmdb_id, season_number)

        season_model = Season.from_json(
            season_data=season_details if season_details else {},
            url=season_url,
            embed_episodes_urls=embed_episode_urls,
        )

        seasons.append(season_model)

    title = film_data.get("name")
    year = tmdb_data.get("first_air_date", "")
    cast = [actor.get("name") for actor in film_data.get("actor", [])]
    description = tmdb_data.get("overview", "")
    poster_path = IMG_HOST + tmdb_data.get("poster_path", "")
    backdrop_path = IMG_HOST + tmdb_data.get("backdrop_path", "")
    rating = tmdb_data.get("vote_average", 0.0)

    return TvSeriesDTO(
        title=title,
        tmdb_id=tmdb_id,
        description=description,
        cast=cast,
        year=year,
        rating=rating,
        posterPath=poster_path,
        backdropPath=backdrop_path,
        seasons=seasons,
    )
