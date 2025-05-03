from typing import Dict, Any
from fastapi import Request
from logger import get_logger

logger = get_logger(__name__)

async def request_to_json(request: Request) -> Dict[str, Any]:
    try:
        body_bytes = await request.body()
        body_json = await request.json()
        logger.debug(f"Request body: {body_json}")
        return body_json
    except Exception as e:
        logger.error(f"Failed to parse request body: {str(e)}")
        return {}