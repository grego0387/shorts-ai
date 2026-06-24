import subprocess
import os
import json
import anthropic
from store import job_store

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def download_video(url: str, job_id: str) -> str:
    output_path = f"/tmp/{job_id}.mp4"
    subprocess.run([
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url
    ], check=True)
    return output_path

def get_video_duration(path: str) -> float:
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", path
    ], capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

def extract_audio_transcript(video_path: str, job_id: str) -> str:
    """Extract audio and get transcript via ffmpeg subtitles or return timecodes."""
    audio_path = f"/tmp/{job_id}.mp3"
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "mp3", "-ar", "16000",
        "-y", audio_path
    ], check=True)
    return audio_path

def analyze_with_claude(duration: float, url: str) -> list:
    """Ask Claude to suggest the best short moments based on video metadata."""
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
    # Strip markdown if present
    text = text.replace("```json", "").replace("```", "").strip()
    clips = json.loads(text)
    return clips

def cut_clip(video_path: str, start: int, end: int, output_path: str):
    """Cut a clip and convert to vertical 9:16 format for Shorts."""
    duration = end - start
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-ss", str(start),
        "-t", str(duration),
        # Scale and pad to 1080x1920 (vertical)
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

        job_store[job_id] = {
            "status": "done",
            "clips": clips
        }

        # Cleanup original
        os.remove(video_path)

    except Exception as e:
        job_store[job_id] = {"status": "error", "error": str(e), "clips": []}
