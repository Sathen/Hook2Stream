import logging
import os

from yt_dlp import YoutubeDL

from settings import DOWNLOAD_DIR

logging.basicConfig(level=logging.INFO)


def download_video(url, filename):
    logging.info(f"Starting download: {filename}")
    output_path = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        'quiet': True,
        'outtmpl': output_path,
        'noprogress': False
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    logging.info(f"✅ Finished downloading: {filename}")


def download_videos(film_name, season, video_urls):
    video_urls = list(filter(lambda x: x is not None, video_urls))
    for index, url in enumerate(video_urls, start=1):
        season_part = f"_S{int(season):02d}" if season else ""
        episode_part = f"_E{index:02d}" if season else ""
        safe_film_name = film_name.replace(" ", "_")
        filename = f"{safe_film_name}/" + f"{safe_film_name}{season_part}{episode_part}.mp4"
        download_video(url, filename)
