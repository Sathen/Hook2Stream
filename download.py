import time
from typing import List

from logger import get_logger
from media_models import LinkTranslator
from stream_extractor import StreamExtractor

logger = get_logger(__name__)

stream_extractor = StreamExtractor()


def get_direct_stream_urls(url: str) -> List[LinkTranslator]:
    start_time = time.time()
    result = stream_extractor.get_stream_urls(url)
    time_elapsed = time.time() - start_time
    logger.info(f"<UNK> Download took {time_elapsed} seconds")
    return result
