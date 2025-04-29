import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
import json

from database import init_db, add_to_db, delete_from_db_by_ids, get_all_data
from localization import get_ukrainian_title
from media_service import add_media, delete_media
from sonarr import get_monitored_seasons
from models import MediaData, extract_fields
from scheduler import start_grab_scheduler, shutdown

app = FastAPI()

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await start_grab_scheduler()
    yield
    await shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/receive/sonarr")
async def receive_full_request(request: Request):
    logging.info(f"Incoming request: {request}")

    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8', errors='replace')

    try:
        body_json = json.loads(body_text)
    except json.JSONDecodeError:
        logging.info("Error parsing Json response")

    media_data: MediaData = await extract_fields(body_json)

    if media_data.event_type == "SeriesAdd" and media_data.tmdb_id:
        await add_media(body_json, media_data)

    if media_data.event_type in ("Grab", "SeriesDelete"):
        await delete_media(media_data)


@app.get("/all")
async def get_all():
    return get_all_data()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3535)
