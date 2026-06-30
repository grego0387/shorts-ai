from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import shutil
from processor import process_uploaded_video
from store import job_store

app = FastAPI(title="Shorts AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Shorts AI running"}

@app.post("/upload")
async def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    video_path = f"/tmp/{job_id}.mp4"

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job_store[job_id] = {"status": "processing", "clips": []}
    background_tasks.add_task(process_uploaded_video, job_id, video_path)
    return {"job_id": job_id}

@app.get("/status/{job_id}")
def status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/download/{job_id}/{clip_id}")
def download_clip(job_id: str, clip_id: int):
    job = job_store.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Clip not found")
    clip = next((c for c in job["clips"] if c["id"] == clip_id), None)
    if not clip or not os.path.exists(clip["file"]):
        raise HTTPException(status_code=404, detail="File not found")
    from fastapi.responses import FileResponse
    return FileResponse(clip["file"], filename=f"{clip['title']}.mp4", media_type="video/mp4")
