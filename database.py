from datetime import datetime, timedelta
from pathlib import Path
import os
import sqlite3
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from models import MediaData
from settings import DB_PATH
from logger import get_logger

logger = get_logger(__name__)

# SQL Queries as constants
CREATE_MEDIA_TABLE = """
    CREATE TABLE IF NOT EXISTS media_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT UNIQUE,
        source_type TEXT NOT NULL,
        internal_id INTEGER UNIQUE,
        created_on TIMESTAMP,
        local_title TEXT,
        tmdbId INTEGER UNIQUE,
        imdbId TEXT UNIQUE,
        tvdbId INTEGER UNIQUE
    )
"""

CREATE_SEASONS_TABLE = """
    CREATE TABLE IF NOT EXISTS monitored_seasons (
        internal_id INTEGER,
        season_number INTEGER,
        PRIMARY KEY (internal_id, season_number),
        FOREIGN KEY (internal_id) REFERENCES media_data(internal_id)
    )
"""

SELECT_MEDIA = """
    SELECT id, title, created_on, tmdbId, imdbId, tvdbId, 
           internal_id, local_title, source_type
    FROM media_data
"""


class DatabaseManager:
    def __init__(self, db_path: str):
        """Initialize database manager and ensure database exists."""
        self.db_path = Path(db_path)
        self._ensure_db_exists()
        self.init_db()

    def _ensure_db_exists(self) -> None:
        """Ensure database file and its directory exist."""
        try:
            # Create parent directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create database file if it doesn't exist
            if not self.db_path.exists():
                logger.info(f"Creating new database at: {self.db_path}")
                self.db_path.touch()
                
        except Exception as e:
            logger.error(f"Failed to create database file: {e}")
            raise

    def get_connection(self):
        """Create and return a database connection with foreign key support."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def init_db(self) -> None:
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_MEDIA_TABLE)
            cursor.execute(CREATE_SEASONS_TABLE)
            conn.commit()

    def add_media(self, media_data: MediaData, monitored_seasons: List[int]) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO media_data 
                    (internal_id, title, source_type, created_on, tmdbId, 
                     imdbId, tvdbId, local_title)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        media_data.internal_id,
                        media_data.series_title,
                        media_data.source_type,
                        media_data.created_on,
                        media_data.tmdb_id,
                        media_data.imdb_id,
                        media_data.tvdb_id,
                        media_data.local_title
                    )
                )
                
                self._add_monitored_seasons(cursor, media_data.internal_id, monitored_seasons)
                return True
                
        except sqlite3.IntegrityError:
            logger.info(f"Media '{media_data.series_title}' already exists")
            return False

    def _add_monitored_seasons(self, cursor: sqlite3.Cursor, internal_id: int, seasons: List[int]) -> None:
        """Add monitored seasons for a media entry."""
        cursor.executemany(
            "INSERT INTO monitored_seasons (internal_id, season_number) VALUES (?, ?)",
            [(internal_id, season) for season in seasons]
        )

    def delete_by_id(self, **kwargs: Dict[str, Any]) -> None:
        """Delete media entry by any of its IDs."""
        id_mapping = {
            'internal_id': 'internal_id',
            'tmdb_id': 'tmdbId',
            'imdb_id': 'imdbId',
            'tvdb_id': 'tvdbId'
        }

        for param, column in id_mapping.items():
            if value := kwargs.get(param):
                with self.get_connection() as conn:
                    conn.execute(f"DELETE FROM media_data WHERE {column} = ?", (value,))
                break

    def get_media_older_than(self, minutes: int) -> List[MediaData]:
        """Get media entries older than specified minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"{SELECT_MEDIA} WHERE created_on <= ?",
                (cutoff_time.strftime("%Y-%m-%d %H:%M:%S"),)
            )
            return [self._map_to_media(row) for row in cursor.fetchall()]

    def get_monitored_seasons(self, internal_id: int) -> List[int]:
        """Get monitored seasons for a media entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT season_number FROM monitored_seasons WHERE internal_id = ? ORDER BY season_number",
                (internal_id,)
            )
            return [row[0] for row in cursor.fetchall()]

    def get_all_media(self) -> List[Dict[str, Any]]:
        """Get all media entries with their monitored seasons."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SELECT_MEDIA)
            
            return [
                {
                    **self._row_to_dict(row),
                    "monitored_seasons": self.get_monitored_seasons(row[6])
                }
                for row in cursor.fetchall()
            ]

    @staticmethod
    def _row_to_dict(row: tuple) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        return {
            "id": row[0],
            "title": row[1],
            "created_on": row[2],
            "tmdbId": row[3],
            "imdbId": row[4],
            "tvdbId": row[5],
            "localTitle": row[7],
            "sourceType": row[8]
        }

    @staticmethod
    def _map_to_media(row: tuple) -> MediaData:
        """Map database row to MediaData object."""
        return MediaData(
            series_title=row[1],
            created_on=row[2],
            event_type=None,
            tmdb_id=row[3],
            imdb_id=row[4],
            tvdb_id=row[5],
            internal_id=row[6],
            local_title=row[7],
            source_type=row[8]
        )


# Create singleton instance
db = DatabaseManager(DB_PATH)

# Maintain backwards compatibility with existing code
def init_db() -> None:
    """Initialize database (compatibility function)."""
    db.init_db()

def add_to_db(media_data: MediaData, monitored_seasons: List[int]) -> None:
    """Add media to database (compatibility function)."""
    db.add_media(media_data, monitored_seasons)

def delete_from_db_by_ids(**kwargs) -> None:
    """Delete media from database (compatibility function)."""
    db.delete_by_id(**kwargs)

def get_media_added_more_than(minutes_ago: int) -> List[MediaData]:
    """Get older media entries (compatibility function)."""
    return db.get_media_older_than(minutes_ago)

def get_monitored_seasons(internal_id: int) -> List[int]:
    """Get monitored seasons (compatibility function)."""
    return db.get_monitored_seasons(internal_id)

def get_all_data() -> List[Dict[str, Any]]:
    """Get all media data (compatibility function)."""
    return db.get_all_media()
