import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from database import init_db, get_all_data
from download import stop_all_downloads
from media_service import add_media, delete_media
from models import MediaData, map_sonarr_response, map_radarr_response
from scheduler import start_grab_scheduler
from logger import get_logger

logger = get_logger(__name__)

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await start_grab_scheduler()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhook/sonarr")
async def sonarr_webhook(request: Request):
    logger.info(f"Sadarr incoming request: {request}")

    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8', errors='replace')

    try:
        body_json = json.loads(body_text)
    except json.JSONDecodeError:
        logger.info("Error parsing Json response")

    media_data: MediaData = await map_sonarr_response(body_json)

    if media_data.event_type == "SeriesAdd" and media_data.tmdb_id:
        await add_media(media_data)

    if media_data.event_type in ("Grab", "SeriesDelete"):
        await delete_media(media_data)


@app.post("/webhook/radarr")
async def radarr_webhook(request: Request):
    logger.info(f"Radarr incoming request: {request}")

    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8', errors='replace')

    try:
        body_json = json.loads(body_text)
    except json.JSONDecodeError:
        logger.info("Error parsing Json response")

    media_data: MediaData = await map_radarr_response(body_json)

    if media_data.event_type == "MovieAdd" and media_data.tmdb_id:
        await add_media(media_data)

    if media_data.event_type in ("Grab", "MovieDelete"):
        await delete_media(media_data)


@app.get("/all")
async def get_all():
    return get_all_data()


@app.get("/download/stop")
async def get_all():
    return stop_all_downloads()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3535)
