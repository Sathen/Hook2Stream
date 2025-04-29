import logging
import os
import subprocess

import database
from settings import DOWNLOAD_DIR

logging.basicConfig(level=logging.INFO)

CURRENT_DOWNLOAD_PROCESS = None


def download_video(internal_id, url, filename):
    global CURRENT_DOWNLOAD_PROCESS

    logging.info(f"🎬 Starting download: {filename}")
    output_path = os.path.join(DOWNLOAD_DIR, filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    command = [
        "yt-dlp",
        "--quiet",
        "--no-progress",
        "-o", output_path,
        url
    ]

    try:
        CURRENT_DOWNLOAD_PROCESS = subprocess.Popen(command)
        CURRENT_DOWNLOAD_PROCESS.wait()
        logging.info(f"✅ Finished downloading: {output_path}")
    except Exception as e:
        logging.error(f"❌ Download failed for {url}: {e}")
    finally:
        CURRENT_DOWNLOAD_PROCESS = None


def stop_current_download():
    global CURRENT_DOWNLOAD_PROCESS
    if CURRENT_DOWNLOAD_PROCESS and CURRENT_DOWNLOAD_PROCESS.poll() is None:
        logging.info("🛑 Interrupting current download...")
        CURRENT_DOWNLOAD_PROCESS.terminate()
        CURRENT_DOWNLOAD_PROCESS = None


def download_videos(internal_id: int, film_name: str, video_urls: list, season: int = None):
    video_urls = list(filter(None, video_urls))
    for index, url in enumerate(video_urls, start=1):
        season_part = f"_S{int(season):02d}" if season else ""
        episode_part = f"_E{index:02d}" if season else ""
        safe_film_name = film_name.replace(" ", "_")
        filename = f"{safe_film_name}/{safe_film_name}{season_part}{episode_part}.mp4"
        download_video(internal_id, url, filename)
