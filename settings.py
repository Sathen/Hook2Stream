import os

SONARR_URL = os.environ.get("SONARR_URL", "https://tv.domcinema.win")
RADARR_URL = os.environ.get("RADARR_URL", "https://movie.domcinema.win")
TMDB_BASE_URL = os.environ.get("TMDB_BASE_URL", "https://api.themoviedb.org/3")
HOST = os.environ.get("HOST", "https://uaserial.top")

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
SONARR_API_KEY = os.environ.get("SONARR_API_KEY", "")
RADARR_API_KEY = os.environ.get("RADARR_API_KEY", "")


DB_PATH = os.environ.get("DB_PATH", "data.db")
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/app/downloads")
SCHEDULER_INTERVAL = os.environ.get("SCHEDULER_INTERVAL", "5")

SEARCH_QUERY = "search?query="
USER_AGENT = os.environ.get("USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
