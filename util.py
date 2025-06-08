import json
from typing import Any

from logger import get_logger
from fastapi import Request

logger = get_logger(__name__)


async def request_to_json(request: Request) -> Any | None:
    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8', errors='replace')

    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        logger.info("Error parsing Json response")
