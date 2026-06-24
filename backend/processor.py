import subprocess
import os
import json
import anthropic
import imageio_ffmpeg
from store import job_store

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
COOKIES = os.environ.get("YOUTUBE_COOKIES", "")

def get_cookies_file() -> str:
    if not COOKIES:
        return None
    cookies_path = "/tmp/yt_cookies.txt"
    with open(cookies_path, "w") as f:
        f.write(COOKIES)
    return cookies_path

def download_video(url: str, job_id: str) -> str:
    output_path = f"/tmp/{job_id}.mp4"
    cookies_path = get_cookies_file()
    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]/best",
        "--ffmpeg-location", FFMPEG,
        "--no-check-certificates",
        "-o", output_path,
        url
    ]
    if cookies_path:
        cmd.insert(1, "--cookies")
        cmd.insert(2, cookies_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"yt-dlp error:
