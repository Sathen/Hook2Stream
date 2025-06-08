import os

TMDB_BASE_URL = os.environ.get("TMDB_BASE_URL", "https://api.themoviedb.org/3")
HOST = os.environ.get("HOST", "https://uaserial.top")
IMG_HOST = "https://image.tmdb.org/t/p/original/"

TMDB_API_KEY = os.environ.get("TMDB_API_KEY",
                              "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlOTYyNDhhM2ExOGI2NTMzN2M5NTVhYjIwZjdlZDIwOCIsIm5iZiI6MTc0NTg3MzIyNC45OTMsInN1YiI6IjY4MGZlOTQ4NWFkMGI2N2M2NmVhZThjZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.J1usuuE2EfsKG2_rbI-MZRg9ubyRaR1g69Mp5UxXCZg")

SEARCH_QUERY = "search?query="
USER_AGENT = os.environ.get("USER_AGENT",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
