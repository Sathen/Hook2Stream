# 🎬 Hook2Stream

**Hook2Stream** is an Python application that listens to **Sonarr** and **Radarr** webhooks, stores added media into a local database, and if the media was not successfully grabbed by Sonarr/Radarr, it searches for the media online, extracts available video streams, and starts downloading them automatically.


**Currently, it supports only Ukrainian online sources for media search and download.**

---

## 🚀 Features

- Listens to `SeriesAdd`, `MovieAdd`, `Grab`, and `SeriesDelete` webhook events from Sonarr/Radarr.
- Saves media metadata (tmdbId, imdbId, tvdbId, internal_id, monitored seasons) into a local SQLite database.
- Periodically checks ungrabbed media and starts external search if needed.
- Supports video stream extraction and downloading via `yt-dlp`.
- Asynchronously handles database and API interactions for maximum performance.

---

## 📦 Installation

```bash
git clone https://github.com/Sathen/Hook2Stream.git
cd Hook2Stream
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

> Make sure you have `yt-dlp` installed and available in your PATH.

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```dotenv
SONARR_API_KEY=your_sonarr_api_key
SONARR_URL=https://your-sonarr-domain.com
RADARR_API_KEY=your_radarr_api_key
RADARR_URL=https://your-radarr-domain.com
TMDB_API_KEY=your_tmdb_api_key
```

Set up **webhooks** in Sonarr and Radarr:
- For Sonarr: `http://your-server-ip:3535/receive/sonarr`
- For Radarr: `http://your-server-ip:3535/receive/radarr`

Make sure your server is reachable from Sonarr/Radarr instance.

---

## 🛠 Usage

Run the application:

```bash
uvicorn main:app --host 0.0.0.0 --port 3535
```

- The server listens for incoming webhooks.
- New media is saved to the database.
- A background scheduler runs every 5 minutes:
  - Selects media older than 3 minutes that is not yet grabbed.
  - Searches for online streams and initiates downloads.

---

## 📋 API Endpoints

| Method | URL | Description |
|:---|:---|:---|
| POST | `/receive/sonarr` | Handle incoming Sonarr webhook |
| POST | `/receive/radarr` | Handle incoming Radarr webhook |
| GET | `/all` | Retrieve all stored media entries |

---

## 📚 Technologies Used

- **FastAPI** — backend server
- **SQLite** — lightweight local database
- **APScheduler** — background job scheduling
- **httpx** — asynchronous HTTP requests
- **yt-dlp** — video stream extraction and download
- **TMDb API** — fetching localized titles (Ukrainian names support)

---

## 🎯 Future Plans

- Integrate torrent search and download as fallback.
- Auto-update Sonarr/Radarr status after manual download.
- Add Telegram/Discord notification integration.
- Improve search engine scraping for more sources.

---

---

## ⚡ License

Free for personal use.  
Please contact the author for commercial usage.