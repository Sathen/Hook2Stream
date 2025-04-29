import logging
import os
import subprocess

from settings import DOWNLOAD_DIR

logging.basicConfig(level=logging.INFO)


def download_video(url, filename):
    logging.info(f"🎬 Starting download: {filename}")
    output_path = os.path.join(DOWNLOAD_DIR, filename)

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    command = [
        "yt-dlp",
        "--quiet",
        "--no-progress",
        "-o", output_path,
        url
    ]

    try:
        subprocess.run(command, check=True)
        logging.info(f"✅ Finished downloading: {output_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Download failed for {url}: {e}")


def download_videos(film_name, season, video_urls):
    video_urls = list(filter(None, video_urls))
    for index, url in enumerate(video_urls, start=1):
        season_part = f"_S{int(season):02d}" if season else ""
        episode_part = f"_E{index:02d}" if season else ""
        safe_film_name = film_name.replace(" ", "_")
        filename = f"{safe_film_name}/{safe_film_name}{season_part}{episode_part}.mp4"
        download_video(url, filename)
