import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from models import MediaData
from sonarr import (
    SonarrClient, 
    RadarrClient, 
    ServiceConfig, 
    MediaClientError
)

@pytest.fixture
def sonarr_client():
    return SonarrClient(ServiceConfig("http://test", "test-key"))

@pytest.fixture
def media_data():
    return MediaData(
        series_title="Test Show",
        internal_id=1,
        tmdb_id=123,
        created_on="2025-05-01"
    )

@pytest.mark.asyncio
async def test_get_monitored_seasons(sonarr_client):
    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"seasons": [
                {"seasonNumber": 1, "monitored": True},
                {"seasonNumber": 2, "monitored": False}
            ]})
        )
        
        seasons = await sonarr_client.get_monitored_seasons(1)
        assert seasons == [1]