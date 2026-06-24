import subprocess
import os
import json
import anthropic
import imageio_ffmpeg
from store import job_store

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def get_cookies_file() -> str:
    cookies_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    if os.path.exists(cookies_path):
        return cookies_path
    return None

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
        raise Exception(f"yt-dlp error: {result.stderr[-500:]}")
    return output_path

def get_video_duration(path: str) -> float:
    ffprobe = FFMPEG.replace("ffmpeg", "ffprobe")
    result = subprocess.run([
        ffprobe, "-v", "quiet",
        "-print_format", "json",
        "-show_format", path
    ], capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

def analyze_with_claude(duration: float, url: str) -> list:
    prompt = f"""You are a viral short-form video expert.
A YouTube video has been uploaded with URL: {url}
Total duration: {duration:.0f} seconds ({duration/60:.1f} minutes).

Generate 5 suggested clip segments that would make great YouTube Shorts / TikToks.
Each clip should be 30-59 seconds long.
Space them throughout the video.

Respond ONLY with a JSON array, no markdown, no explanation:
[
  {{"title": "clip title", "start": 0, "end": 55, "score": 94, "reason": "why this moment is exciting"}},
  ...
]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def cut_clip(video_path: str, start: int, end: int, output_path: str):
    duration = end - start
    subprocess.run([
        FFMPEG, "-i", video_path,
        "-ss", str(start),
        "-t", str(duration),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-y", output_path
    ], check=True)

def process_video(job_id: str, url: str):
    try:
        job_store[job_id]["status"] = "downloading"
        video_path = download_video(url, job_id)

        job_store[job_id]["status"] = "analyzing"
        duration = get_video_duration(video_path)
        clips_meta = analyze_with_claude(duration, url)

        job_store[job_id]["status"] = "cutting"
        clips = []
        for i, clip in enumerate(clips_meta):
            out_path = f"/tmp/{job_id}_clip_{i}.mp4"
            cut_clip(video_path, clip["start"], clip["end"], out_path)
            clips.append({
                "id": i,
                "title": clip["title"],
                "start": clip["start"],
                "end": clip["end"],
                "score": clip["score"],
                "reason": clip["reason"],
                "file": out_path
            })

        job_store[job_id] = {"status": "done", "clips": clips}
        os.remove(video_path)

    except Exception as e:
        job_store[job_id] = {"status": "error", "error": str(e), "clips": []}
