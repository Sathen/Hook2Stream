import pytest
from datetime import datetime
from models import (
    MediaData,
    MediaSourceType,
    SonarrMapper,
    RadarrMapper,
    map_radarr_response,
    map_sonarr_response
)

@pytest.fixture
def sonarr_webhook_data():
    return {
        "eventType": "Grabbed",
        "series": {
            "id": 1,
            "title": "Test Show",
            "tmdbId": 123,
            "imdbId": "tt1234567",
            "tvdbId": 789
        }
    }

@pytest.fixture
def radarr_webhook_data():
    return {
        "eventType": "Grabbed",
        "movie": {
            "id": 1,
            "title": "Test Movie",
            "tmdbId": 123,
            "imdbId": "tt1234567"
        }
    }

@pytest.mark.asyncio
async def test_sonarr_mapping(sonarr_webhook_data):
    media_data = await map_sonarr_response(sonarr_webhook_data)
    assert media_data.internal_id == 1
    assert media_data.series_title == "Test Show"
    assert media_data.source_type == MediaSourceType.SONARR.value

@pytest.mark.asyncio
async def test_radarr_mapping(radarr_webhook_data):
    media_data = await map_radarr_response(radarr_webhook_data)
    assert media_data.internal_id == 1
    assert media_data.series_title == "Test Movie"
    assert media_data.source_type == MediaSourceType.RADARR.value