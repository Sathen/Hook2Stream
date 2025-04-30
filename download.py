import os
import signal
import subprocess
import threading

from settings import DOWNLOAD_DIR
from logger import get_logger

logger = get_logger(__name__)

running_processes = []
process_lock = threading.Lock()
stop_flag = threading.Event()


def is_aborted():
    return not stop_flag.is_set()


def reset():
    stop_flag.clear()


def start_subprocess(command: list) -> subprocess.Popen:
    return subprocess.Popen(
        command,
        preexec_fn=os.setsid,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )


def download_video(url, filename) -> bool:
    global running_processes

    logger.info(f"🎬 Starting download: {filename}")
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
        process = start_subprocess(command)
        with process_lock:
            running_processes.append(process)
        for line in process.stdout:
            logger.info(f"[yt-dlp] {line.strip()}")
        logger.info(f"✅ Finished downloading: {output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Download failed for {url}: {e}")
        return False
    finally:
        with process_lock:
            if process in running_processes:
                running_processes.remove(process)


def stop_all_downloads():
    for proc in running_processes:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                stop_flag.set()
            except Exception as e:
                print(f"Failed to kill {proc.pid}: {e}")


def download_videos(film_name: str, video_urls: list, season: int = None):
    video_urls = list(filter(None, video_urls))
    safe_film_name = film_name.replace(" ", "_")
    download_folder = f"{safe_film_name}/"
    for index, url in enumerate(video_urls, start=1):
        if is_aborted():
            season_part = f"_S{int(season):02d}" if season else ""
            episode_part = f"_E{index:02d}" if season else ""
            filename = download_folder + f"{safe_film_name}{season_part}{episode_part}.mp4"
            download_video(url, filename)

    reset()
    return download_folder
