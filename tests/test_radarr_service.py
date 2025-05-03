import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from service.radarr_service import handle_ranarr_media
from models import MediaData

# filepath: /Users/ilonaholikova/PycharmProjects/Hook2Stream/service/test_radarr_service.py


@pytest.mark.asyncio
async def test_handle_ranarr_media():
    # Mock dependencies
    mock_search_film = MagicMock(return_value=["link1", "link2"])
    mock_download_videos = AsyncMock(return_value="/path/to/downloaded/file")
    mock_is_aborted = MagicMock(return_value=False)
    mock_tell_radarr_manual_import = AsyncMock()

    # Patch the dependencies
    with patch("service.search_links.search_film", mock_search_film), \
         patch("service.download.download_videos", mock_download_videos), \
         patch("service.download.is_aborted", mock_is_aborted), \
         patch("service.sonarr.tell_radarr_manual_import", mock_tell_radarr_manual_import):
        
        # Create a mock MediaData object
        media = MediaData(series_title="Test Movie", local_title="test_movie")

        # Call the function
        await handle_ranarr_media(media)

        # Assertions
        mock_search_film.assert_called_once_with(media)
        mock_download_videos.assert_awaited_once_with("test_movie", ["link1", "link2"])
        mock_is_aborted.assert_called_once()
        mock_tell_radarr_manual_import.assert_awaited_once_with(media, "/path/to/downloaded/file")