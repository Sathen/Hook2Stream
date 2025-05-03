import os

SONARR_URL = os.environ.get("SONARR_URL", "https://tv.domcinema.win")
RADARR_URL = os.environ.get("RADARR_URL", "https://movie.domcinema.win")
TMDB_BASE_URL = os.environ.get("TMDB_BASE_URL", "https://api.themoviedb.org/3")
HOST = os.environ.get("HOST", "https://uaserial.top")

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlOTYyNDhhM2ExOGI2NTMzN2M5NTVhYjIwZjdlZDIwOCIsIm5iZiI6MTc0NTg3MzIyNC45OTMsInN1YiI6IjY4MGZlOTQ4NWFkMGI2N2M2NmVhZThjZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.J1usuuE2EfsKG2_rbI-MZRg9ubyRaR1g69Mp5UxXCZg")
SONARR_API_KEY = os.environ.get("SONARR_API_KEY", "3c99d6d0c3d64c81883aa145d66731f8")
RADARR_API_KEY = os.environ.get("RADARR_API_KEY", "f930210870bd4c3d862567ebe1dc6138")


DB_PATH = os.environ.get("DB_PATH", "db/data.db")
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")
SCHEDULER_INTERVAL = os.environ.get("SCHEDULER_INTERVAL", "5")

SEARCH_QUERY = "search?query="
USER_AGENT = os.environ.get("USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
