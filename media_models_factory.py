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

    # Check if we need to split merged seasons
    source_season_count = len(seasons_data)
    tmdb_season_count = await get_tmdb_season_count(tmdb_id)

    # Get available TMDB seasons for splitting/fallback
    available_tmdb_seasons = []
    if tmdb_season_count > 0:
        for season_num in range(1, tmdb_season_count + 1):
            tmdb_season = await tmdb_client.get_tmdb_season(tmdb_id, season_num)
            if tmdb_season:
                available_tmdb_seasons.append(tmdb_season)

    # Determine strategy based on season count mismatch
    split_seasons_data = []
    if tmdb_season_count == 1 and source_season_count > 1 and available_tmdb_seasons:
        # TMDB has merged seasons - split them
        split_seasons_data = await split_merged_season_data(available_tmdb_seasons[0], seasons_data)
        print(f"Split TMDB merged season for series {tmdb_id}: {source_season_count} seasons expected")
    elif tmdb_season_count < source_season_count and available_tmdb_seasons:
        # TMDB has fewer seasons - extend available seasons to cover missing ones
        split_seasons_data = await extend_tmdb_seasons(available_tmdb_seasons, seasons_data, tmdb_data)
        print(f"Extended TMDB seasons for series {tmdb_id}: {tmdb_season_count} -> {source_season_count} seasons")

    seasons = []
    for i, season in enumerate(seasons_data):
        season_number = season.get("seasonNumber")
        season_url = season.get("url")
        embed_episode_urls = await get_tv_embed_urls(season_url)

        # Use processed season data if available
        if split_seasons_data and i < len(split_seasons_data):
            season_details = split_seasons_data[i]
        else:
            # Try to get season from TMDB normally
            season_details = await tmdb_client.get_tmdb_season(tmdb_id, season_number)

            # Create stubbed version if TMDB doesn't have this season
            if not season_details:
                season_details = create_stubbed_season_data(
                    season_number, len(embed_episode_urls), tmdb_data
                )
                print(f"Created stubbed season {season_number} for series {tmdb_id}")

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


async def get_tmdb_season_count(tmdb_id: int) -> int:
    """Get the number of seasons available in TMDB for a series."""
    try:
        # This assumes your tmdb_client has a method to get series details
        series_details = await tmdb_client.get_series_details(tmdb_id)
        return series_details.get("number_of_seasons", 0)
    except:
        # Fallback: try to get seasons 1-10 and count how many exist
        season_count = 0
        for season_num in range(1, 11):  # Check first 10 seasons
            season_data = await tmdb_client.get_tmdb_season(tmdb_id, season_num)
            if season_data:
                season_count += 1
            else:
                break
        return season_count


async def handle_missing_season_data(tmdb_id: int, season_number: int, episode_count: int, tmdb_data: Any) -> dict:

    # Option 1: Try to get all seasons and find the best match
    all_seasons = await tmdb_client.get_all_seasons(tmdb_id)

    if all_seasons:
        # Look for a season that might contain episodes for this season
        best_match = find_best_season_match(all_seasons, season_number, episode_count)
        if best_match:
            return best_match

    # Option 2: Create synthetic season data based on series info
    return create_synthetic_season_data(season_number, episode_count, tmdb_data)


def find_best_season_match(all_seasons: list, target_season: int, target_episode_count: int) -> dict:
    for season in all_seasons:
        if season.get("season_number") == target_season:
            return season

    episode_count_matches = []
    for season in all_seasons:
        season_episode_count = season.get("episode_count", 0)
        if abs(season_episode_count - target_episode_count) <= 5:  # Allow some variance
            episode_count_matches.append(season)

    if episode_count_matches:
        return episode_count_matches[0]

    if target_season <= 2 and all_seasons:
        return all_seasons[0]

    return None


async def extend_tmdb_seasons(available_seasons: list, source_seasons: list, tmdb_data: Any) -> list:
    extended_seasons = []

    for i, source_season in enumerate(source_seasons):
        season_number = source_season.get("seasonNumber", i + 1)
        season_url = source_season.get("url", "")

        # Get episode count from source
        embed_episode_urls = await get_tv_embed_urls(season_url)
        episode_count = len(embed_episode_urls)

        if i < len(available_seasons):
            # Use available TMDB season data
            season_data = available_seasons[i].copy()
            season_data["season_number"] = season_number
            # Update episode count if different
            if season_data.get("episode_count", 0) != episode_count:
                season_data["episode_count"] = episode_count
                # Adjust episodes list if needed
                existing_episodes = season_data.get("episodes", [])
                if len(existing_episodes) != episode_count:
                    season_data["episodes"] = create_episode_stubs(
                        season_number, episode_count, existing_episodes
                    )
        else:
            # Create stubbed season for missing ones
            season_data = create_stubbed_season_data(season_number, episode_count, tmdb_data)

        extended_seasons.append(season_data)

    return extended_seasons


def create_stubbed_season_data(season_number: int, episode_count: int, tmdb_data: Any) -> dict:
    return {
        "id": f"stub_{tmdb_data.get('id', 0)}_{season_number}",
        "season_number": season_number,
        "episode_count": episode_count,
        "name": f"Season {season_number}",
        "overview": tmdb_data.get("overview", "")[:200] + "..." if tmdb_data.get("overview", "") else "",
        "poster_path": tmdb_data.get("poster_path", ""),
        "air_date": tmdb_data.get("first_air_date", ""),
        "vote_average": tmdb_data.get("vote_average", 0.0),
        "episodes": create_episode_stubs(season_number, episode_count)
    }


def create_episode_stubs(season_number: int, episode_count: int, existing_episodes: list = None) -> list:
    episodes = []

    for i in range(1, episode_count + 1):
        # Use existing episode data if available
        if existing_episodes and i <= len(existing_episodes):
            episode = existing_episodes[i - 1].copy()
            episode["episode_number"] = i
        else:
            # Create stub episode
            episode = {
                "id": f"stub_ep_{season_number}_{i}",
                "episode_number": i,
                "name": f"Episode {i}",
                "overview": "",
                "air_date": "",
                "still_path": "",
                "vote_average": 0.0,
                "vote_count": 0
            }

        episodes.append(episode)

    return episodes


def create_synthetic_season_data(season_number: int, episode_count: int, tmdb_data: Any) -> dict:
    return {
        "id": f"synthetic_{tmdb_data.get('id', 0)}_{season_number}",
        "season_number": season_number,
        "episode_count": episode_count,
        "name": f"Season {season_number}",
        "overview": tmdb_data.get("overview", ""),
        "poster_path": tmdb_data.get("poster_path", ""),
        "air_date": tmdb_data.get("first_air_date", ""),
        "episodes": [
            {
                "id": f"synthetic_ep_{season_number}_{i}",
                "episode_number": i,
                "name": f"Episode {i}",
                "overview": "",
                "air_date": "",
                "still_path": ""
            }
            for i in range(1, episode_count + 1)
        ]
    }


# Alternative approach: Split merged seasons
async def split_merged_season_data(tmdb_season_data: dict, source_seasons: list) -> list:
    """
    Split a merged TMDB season into multiple seasons based on source data.

    Args:
        tmdb_season_data: TMDB season data with all episodes
        source_seasons: List of seasons from your source with episode counts

    Returns:
        List of season data split according to source structure
    """
    episodes = tmdb_season_data.get("episodes", [])
    total_episodes = len(episodes)

    # Calculate expected episodes per season from source
    source_episode_counts = [len(await get_tv_embed_urls(s.get("url", ""))) for s in source_seasons]
    expected_total = sum(source_episode_counts)

    if total_episodes != expected_total:
        # Episode count mismatch - log warning or handle as needed
        print(f"Warning: TMDB has {total_episodes} episodes, source has {expected_total}")

    split_seasons = []
    episode_index = 0

    for i, source_season in enumerate(source_seasons):
        season_episode_count = source_episode_counts[i]
        season_episodes = episodes[episode_index:episode_index + season_episode_count]

        # Create season data for this split
        season_data = {
            **tmdb_season_data,
            "season_number": source_season.get("seasonNumber", i + 1),
            "episode_count": len(season_episodes),
            "episodes": season_episodes
        }

        split_seasons.append(season_data)
        episode_index += season_episode_count

    return split_seasons
