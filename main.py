import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from cache import use_cache
from logger import get_logger
from media_models import StreamsSearchRequest, SearchItem
from service import search_service
from util import request_to_json

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/online/search")
async def search_media(name: str):
    logger.info(f"Search incoming request: {name}")
    result = use_cache(f"online_get:{name}",
                       expire=60,
                       func=lambda: search_service.search(name))
    return result


@app.post("/online/get")
async def get_media(request: Request):
    logger.info(f"Get incoming request: {request}")
    json = await request_to_json(request)
    search_request = SearchItem.from_json(json)
    result = await search_service.get_media(search_request)
    return result


@app.get("/online/videos")
async def get_videos(path: str):
    result = await search_service.get_videos(path)
    return result


@app.post("/online/film-streams")
async def get_film_streams_endpoint(request: Request):
    logger.info(f"Get incoming request: {request.url}")
    start_time = time.time()
    json = await request_to_json(request)
    search_request = StreamsSearchRequest.from_json(json)
    result = await search_service.new_get_film_streams(search_request)
    logger.info(f"Get film streams request time: {time.time() - start_time}")
    logger.info(f"Get film streams result: {result}")
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3535)
