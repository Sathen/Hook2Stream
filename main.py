from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from util import request_to_json
from database import init_db, get_all_data
from download import stop_all_downloads
from service.media_service import add_media, delete_media
from models import MediaData, map_sonarr_response, map_radarr_response
from scheduler import start_grab_scheduler
from logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    try:
        logger.info("Initializing application...")
        init_db()
        await start_grab_scheduler()
        yield
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    finally:
        logger.info("Shutting down application...")

app = FastAPI(
    title="Hook2Stream",
    description="Media management and download automation",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/webhook/sonarr")
async def sonarr_webhook(request: Request) -> JSONResponse:
    """Handle Sonarr webhook requests."""
    try:
        body_json = await request_to_json(request)
        logger.info(f"Sonarr incoming request: {body_json}")

        media_data = await map_sonarr_response(body_json)
        await handle_media(media_data)
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "title": media_data.series_title}
        )
    except Exception as e:
        logger.error(f"Sonarr webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/radarr")
async def radarr_webhook(request: Request) -> JSONResponse:
    """Handle Radarr webhook requests."""
    try:
        body_json = await request_to_json(request)
        logger.info(f"Radarr incoming request: {body_json}")

        media_data = await map_radarr_response(body_json)
        await handle_media(media_data)
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "title": media_data.series_title}
        )
    except Exception as e:
        logger.error(f"Radarr webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_media(media: MediaData) -> None:
    """Process media based on event type."""
    try:
        if media.event_type in ("MovieAdded", "SeriesAdd") and media.tmdb_id:
            await add_media(media)
        elif media.event_type in ("Grab", "MovieDelete", "SeriesDelete"):
            await delete_media(media)
    except Exception as e:
        logger.error(f"Failed to handle media {media.series_title}: {str(e)}")
        raise

@app.get("/all")
async def get_all() -> Dict[str, Any]:
    """Get all media data."""
    try:
        return {"status": "success", "data": get_all_data()}
    except Exception as e:
        logger.error(f"Failed to get all data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/stop")
async def stop_downloads() -> Dict[str, str]:
    """Stop all active downloads."""
    try:
        stop_all_downloads()
        return {"status": "success", "message": "All downloads stopped"}
    except Exception as e:
        logger.error(f"Failed to stop downloads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3535,
        reload=True,
        log_level="info"
    )
