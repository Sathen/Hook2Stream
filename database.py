from datetime import datetime, timedelta
import sqlite3
from typing import List
from models import MediaData
from settings import DB_PATH
import logging


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                internal_id INTEGER UNIQUE,
                created_on TIMESTAMP,
                local_title TEXT,
                tmdbId INTEGER UNIQUE,
                imdbId TEXT UNIQUE,
                tvdbId INTEGER UNIQUE
            )
        """)
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
              monitored_seasons: List[int], local_title: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        try:
            cursor.execute("""
                INSERT INTO media_data (internal_id, title, created_on, tmdbId, imdbId, tvdbId, local_title)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (internal_id, title, date, tmdb_id, imdb_id, tvdb_id, local_title))
            for season in monitored_seasons:
                cursor.execute("""
                    INSERT INTO monitored_seasons (internal_id, season_number)
                    VALUES (?, ?)
                """, (internal_id, season))
            conn.commit()
        except sqlite3.IntegrityError:
            logging.info(f"{title} already exists. Skipping insert.")


def delete_from_db_by_ids(internal_id: int = None, tmdbId: int = None, imdbId: str = None, tvdbId: int = None):
    with sqlite3.connect(DB_PATH) as conn:
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


def get_media_added_more_than(minutes_ago: int) -> List[MediaData]:
    cutoff_time = datetime.now() - timedelta(minutes=minutes_ago)
    cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, created_on, tmdbId, imdbId, tvdbId, internal_id, local_title
            FROM media_data
            WHERE created_on <= ?
        """, (cutoff_str,))

        media_list = [map_media(row) for row in cursor.fetchall()]

    return media_list


def get_monitored_seasons(internal_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
                SELECT season_number FROM monitored_seasons WHERE internal_id = ? ORDER BY season_number
            """, (internal_id,))
        seasons_rows = cursor.fetchall()
        return [season[0] for season in seasons_rows]


def get_all_data():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_on, tmdbId, imdbId, tvdbId, internal_id, local_title FROM media_data")
        rows = cursor.fetchall()

        media_list = []
        for row in rows:
            cursor.execute("""
                SELECT season_number FROM monitored_seasons WHERE internal_id = ? ORDER BY season_number
            """, (row[6],))
            seasons_rows = cursor.fetchall()
            monitored_seasons = [season[0] for season in seasons_rows]

            media_list.append({
                "id": row[0],
                "title": row[1],
                "created_on": row[2],
                "tmdbId": row[3],
                "imdbId": row[4],
                "tvdbId": row[5],
                "localTitle": row[7],
                "monitored_seasons": monitored_seasons
            })

    return media_list


def map_media(row) -> MediaData:
    return MediaData(
        series_title=row[1],
        date=row[2],
        event_type=None,
        tmdb_id=row[3],
        imdb_id=row[4],
        tvdb_id=row[5],
        internal_id=row[6],
        local_title=row[7]
    )
