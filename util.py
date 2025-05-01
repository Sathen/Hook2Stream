import json
from logger import get_logger
from fastapi import Request

logger = get_logger(__name__)


def request_to_json(request: Request):
    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8', errors='replace')

    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        logger.info("Error parsing Json response")