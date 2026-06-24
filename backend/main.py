from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from processor import process_video
from store import job_store

app = FastAPI(title="Shorts AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def root():
    return {"status": "Shorts AI running"}

@app.post("/analyze")
async def analyze(req: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "processing", "clips": []}
    background_tasks.add_task(process_video, job_id, req.url)
    return {"job_id": job_id}

@app.get("/status/{job_id}")
def status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
