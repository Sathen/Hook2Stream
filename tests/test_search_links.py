import pytest
from unittest.mock import Mock, patch
from models import MediaData
from search_links import VideoSearchClient, VideoSearchError

@pytest.fixture
def video_client():
    return VideoSearchClient()

@pytest.mark.asyncio
async def test_search_film(video_client):
    media = MediaData(
        series_title="Test Show",
        local_title="Test Show UA",
        internal_id=1,
        source_type="TV"
    )
    
    with patch('search_links.VideoSearchClient._get_document') as mock_get:
        mock_get.return_value = Mock(
            select_one=Mock(return_value={'href': '/test-show'})
        )
        
        links = video_client.search_film(media)
        assert isinstance(links, list)