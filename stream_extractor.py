# Option 7: Reusable YoutubeDL instance (best for multiple calls)
from functools import lru_cache
from typing import List, Dict

import yt_dlp
from rangedict import RangeDict

from media_models import LinkTranslator

QUALITY_MAP = RangeDict[int, str]()
QUALITY_MAP[(0, 480)] = '480p'
QUALITY_MAP[(481, 720)] = '720p'
QUALITY_MAP[(721, 1080)] = '1080p'


from logger import get_logger

logger = get_logger(__name__)

class StreamExtractor:

    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
            'socket_timeout': 8,
            'retries': 1,
            'fragment_retries': 0,
        }
        self.ydl = yt_dlp.YoutubeDL(self.ydl_opts)

    @lru_cache(maxsize=None)
    def get_stream_urls(self, url: str) -> List[LinkTranslator]:
        try:
            info = self.ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            return [
                LinkTranslator(quality=QUALITY_MAP[fmt['height']], url=fmt['url'])
                for fmt in formats
                if fmt.get('height') in QUALITY_MAP and fmt.get('url')
            ]

        except Exception as e:
            logger.error(f"Stream extraction failed for {url}: {str(e)}")
            return []

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'ydl'):
            self.ydl.close()