import pytest
from unittest.mock import patch, AsyncMock

from models import MediaData
from service.media_service import (
    add_media,
    delete_media,
    MediaServiceError
)

@pytest.fixture
def media_data():
    return MediaData(
        internal_id=1,
        series_title="Test Show",
        tmdb_id=123,
        imdb_id="tt1234567",
        tvdb_id=789,
        source_type="SONARR",
        created_on="2025-05-01T12:00:00"
    )

@pytest.mark.asyncio
async def test_add_media(media_data):
    with patch('sonarr.get_monitored_seasons', new_callable=AsyncMock) as mock_seasons, \
         patch('localization.get_ukrainian_title', new_callable=AsyncMock) as mock_title, \
         patch('database.add_to_db') as mock_add:
        
        mock_seasons.return_value = [1, 2]
        mock_title.return_value = "Тестовий серіал"
        
        await add_media(media_data)
        
        assert media_data.local_title == "Тестовий серіал"
        mock_add.assert_called_once_with(media_data, [1, 2])

@pytest.mark.asyncio
async def test_delete_media(media_data):
    with patch('database.delete_from_db_by_ids') as mock_delete:
        await delete_media(media_data)
        
        mock_delete.assert_called_once_with(
            internal_id=1,
            tmdb_id=123,
            imdb_id="tt1234567",
            tvdb_id=789
        )