import logging
from typing import List
import httpx

from fastapi import FastAPI, Request, requests
import sqlite3
import json
from datetime import datetime

app = FastAPI()

db_path = "data.db"
logging.basicConfig(level=logging.INFO)

SONARR_API_KEY = "3c99d6d0c3d64c81883aa145d66731f8"
SONARR_URL = "https://tv.domcinema.win"  # Change if your Sonarr runs elsewhere


async def get_monitored_seasons(series_id: int):
    url = f"{SONARR_URL}/api/v3/series/{series_id}"
    headers = {
        "X-Api-Key": SONARR_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()  # Will raise exception if Sonarr not available

    series_data = response.json()

    monitored_seasons = [
        season["seasonNumber"]
        for season in series_data.get("seasons", [])
        if season.get("monitored", False)
    ]

    return monitored_seasons


def init_db():
    """Initialize database table if it doesn't exist"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                internal_id INTEGER UNIQUE, 
                created_on TIMESTAMP,
                tmdbId INTEGER UNIQUE,
                imdbId TEXT UNIQUE,
                tvdbId INTEGER UNIQUE
            )
        """)

        # Create monitored_seasons table
        cursor.execute("""
                   CREATE TABLE IF NOT EXISTS monitored_seasons (
                       internal_id INTEGER,
                       season_number INTEGER,
                       PRIMARY KEY (internal_id, season_number),
                       FOREIGN KEY (internal_id) REFERENCES media_data(internal_id)
                   )
               """)
        conn.commit()


def add_to_db(internal_id: int, title: str, date: str, tmdb_id: int, imdb_id: str, tvdb_id: int,
              monitored_seasons: List[int]):
    """Add a record to the database and insert monitored seasons"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")  # Make sure foreign keys are enforced

        try:
            cursor.execute("""
                INSERT INTO media_data (internal_id, title, created_on, tmdbId, imdbId, tvdbId)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (internal_id, title, date, tmdb_id, imdb_id, tvdb_id))

            # Insert monitored seasons
            for season in monitored_seasons:
                cursor.execute("""
                    INSERT INTO monitored_seasons (internal_id, season_number)
                    VALUES (?, ?)
                """, (internal_id, season))

            conn.commit()

        except sqlite3.IntegrityError:
            logging.info(f"{title} already exists. Skipping insert.")


def delete_from_db_by_id(internal_id: int = None, tmdbId: int = None, imdbId: str = None, tvdbId: int = None):
    """Delete a record from the database by one of the provided IDs"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        if tmdbId:
            cursor.execute("DELETE FROM media_data WHERE tmdbId = ?", (tmdbId,))
        elif imdbId:
            cursor.execute("DELETE FROM media_data WHERE imdbId = ?", (imdbId,))
        elif tvdbId:
            cursor.execute("DELETE FROM media_data WHERE tvdbId = ?", (tvdbId,))
        elif internal_id:
            cursor.execute("DELETE FROM media_data WHERE internal_id = ?", (internal_id,))
        conn.commit()


@app.post("/receive/sonarr")
async def receive_full_request(request: Request):
    logging.info(f"Request: {request}")
    # Read raw body
    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8', errors='replace')

    try:
        body_json = json.loads(body_text)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON received"}

    internal_id, date, event_type, imdb_id, series_title, tmdb_id, tvdb_id = await extract_fields(body_json)

    if event_type == "SeriesAdd" and series_title:
        logging.info(f"{body_json}")
        seasons = await get_monitored_seasons(internal_id)
        add_to_db(internal_id, series_title, date, tmdb_id, imdb_id, tvdb_id, seasons)
        logging.info(f"Add {series_title} with tmdb: {tmdb_id} imdb: {imdb_id} tvdb: {tvdb_id}")

    # If eventType is "Grab", delete the record by one of the IDs
    if event_type == "Grab" or event_type == "SeriesDelete":
        if tmdb_id or imdb_id or tvdb_id:
            delete_from_db_by_id(internal_id, tmdb_id, imdb_id, tvdb_id)
            logging.info(f"Add {series_title} with tmdb: {tmdb_id} imdb: {imdb_id} tvdb: {tvdb_id}")
        else:
            logging.info(f"No valid ID provided for Grab event for title {series_title}")


@app.get("/all")
async def get_all_data():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # First query: get all media data
        cursor.execute("SELECT id, title, created_on, tmdbId, imdbId, tvdbId, internal_id FROM media_data")
        rows = cursor.fetchall()

        media_list = []

        # For each media entry, fetch its monitored seasons
        for row in rows:
            media_id = row[0]
            title = row[1]
            created_on = row[2]
            tmdb_id = row[3]
            imdb_id = row[4]
            tvdb_id = row[5]
            internal_id = row[6]

            # Second query: fetch seasons for this media
            cursor.execute("""
                        SELECT season_number
                        FROM monitored_seasons
                        WHERE internal_id = ?
                        ORDER BY season_number
                    """, (internal_id,))
            seasons_rows = cursor.fetchall()
            monitored_seasons = [season[0] for season in seasons_rows]

            # Append data to media list
            media_list.append({
                "id": media_id,
                "title": title,
                "created_on": created_on,
                "tmdbId": tmdb_id,
                "imdbId": imdb_id,
                "tvdbId": tvdb_id,
                "monitored_seasons": monitored_seasons
            })

    return media_list


async def extract_fields(body_json):
    # Extract fields safely
    event_type = body_json.get("eventType")
    series_title = None
    internal_id = None
    date = None
    tmdb_id = None
    imdb_id = None
    tvdb_id = None
    if "series" in body_json and isinstance(body_json["series"], dict):
        series_title = body_json["series"].get("title")
        date = body_json["series"].get("date", str(datetime.now()))  # Defaults to current time if missing
        tmdb_id = body_json["series"].get("tmdbId")
        internal_id = body_json["series"].get("id")
        imdb_id = body_json["series"].get("imdbId")
        tvdb_id = body_json["series"].get("tvdbId")
    return internal_id, date, event_type, imdb_id, series_title, tmdb_id, tvdb_id


if __name__ == "__main__":
    init_db()  # Ensure DB and table are initialized before starting the server
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3535)
