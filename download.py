import os
import signal
import subprocess
import threading
from typing import List, Optional
from pathlib import Path

from logger import get_logger
from settings import DOWNLOAD_DIR

logger = get_logger(__name__)

# Constants
YT_DLP_COMMAND = ["yt-dlp", "--quiet", "--no-progress"]
VIDEO_EXTENSION = ".mp4"

# Global state
running_processes: List[subprocess.Popen] = []
process_lock = threading.Lock()
stop_flag = threading.Event()


class DownloadError(Exception):
    """Custom exception for download failures."""
    pass


def start_subprocess(command: List[str]) -> subprocess.Popen:
    """Start a subprocess with the given command."""
    return subprocess.Popen(
        command,
        preexec_fn=os.setsid,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )


def download_video(url: str, filename: Path) -> bool:
    logger.info(f"🎬 Starting download: {filename}")
    
    command = [*YT_DLP_COMMAND, "-o", str(filename), url]
    process = None

    try:
        process = start_subprocess(command)
        with process_lock:
            running_processes.append(process)

        for line in process.stdout:
            logger.info(f"[yt-dlp] {line.strip()}")

        if process.wait() != 0:
            raise DownloadError(f"yt-dlp failed with exit code {process.returncode}")

        logger.info(f"✅ Finished downloading: {filename}")
        return True

    except Exception as e:
        logger.error(f"❌ Download failed for {url}: {str(e)}")
        return False

    finally:
        if process:
            with process_lock:
                if process in running_processes:
                    running_processes.remove(process)


def stop_all_downloads() -> None:
    """Stop all running download processes."""
    with process_lock:
        for proc in running_processes:
            if proc.poll() is None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    stop_flag.set()
                    logger.info(f"Stopped process {proc.pid}")
                except Exception as e:
                    logger.error(f"Failed to kill process {proc.pid}: {e}")


def download_videos(film_name: str, video_urls: List[str], season: Optional[int] = None) -> Path:
    # Filter out empty URLs and create safe filename
    video_urls = list(filter(None, video_urls))
    safe_film_name = film_name.replace(" ", "_")
    download_folder = Path(DOWNLOAD_DIR) / safe_film_name
    download_folder.mkdir(parents=True, exist_ok=True)

    try:
        for index, url in enumerate(video_urls, start=1):
            if is_aborted():
                logger.warning("Download aborted by user")
                break

            # Build filename with season/episode if applicable
            season_part = f"_S{season:02d}" if season else ""
            episode_part = f"_E{index:02d}" if season else ""
            filename = download_folder / f"{safe_film_name}{season_part}{episode_part}{VIDEO_EXTENSION}"

            if not download_video(url, filename):
                logger.error(f"Failed to download episode {index}")

    finally:
        reset()

    return download_folder


def is_aborted() -> bool:
    """Check if downloads should be aborted."""
    return not stop_flag.is_set()


def reset() -> None:
    """Reset the stop flag."""
    stop_flag.clear()
