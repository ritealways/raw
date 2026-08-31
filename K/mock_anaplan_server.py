"""
Mock Anaplan Server - FastAPI Backend
Simulates Anaplan API endpoints for data ingestion and output retrieval
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
import shutil
import json
import time
from datetime import datetime
from pathlib import Path

# Create directories
UPLOAD_DIR = Path("anaplan_uploads")
OUTPUT_DIR = Path("anaplan_outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Mock Anaplan Server",
    description="Simulates Anaplan API for Streamlit integration",
    version="1.0.0"
)

# In-memory store for jobs and data
jobs_db: Dict[str, Dict[str, Any]] = {}
data_store: Dict[str, Any] = {}


# ==================== MODELS ====================

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    created_at: str
    updated_at: str
    message: str
    input_file: Optional[str] = None
    output_file: Optional[str] = None


class DataPayload(BaseModel):
    model_name: str
    workspace_id: str
    model_id: str
    data: Dict[str, Any]


class ForecastOutput(BaseModel):
    job_id: str
    forecast_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


# ==================== HELPER FUNCTIONS ====================

def generate_job_id() -> str:
    """Generate unique job ID"""
    return f"JOB-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{int(time.time() * 1000) % 10000}"


def create_job(input_filename: str = None) -> str:
    """Create a new job entry"""
    job_id = generate_job_id()
    now = datetime.now().isoformat()
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "message": "Job created, waiting for input data",
        "input_file": input_filename,
        "output_file": None,
        "output_data": None
    }
    return job_id


# ==================== API ENDPOINTS ====================

@app.get("/")
def root():
    """Health check"""
    return {
        "service": "Mock Anaplan Server",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/v1/upload",
            "jobs": "GET /api/v1/jobs",
            "job_status": "GET /api/v1/jobs/{job_id}",
            "download": "GET /api/v1/download/{job_id}",
            "push_output": "POST /api/v1/output/{job_id}"
        }
    }


@app.post("/api/v1/upload", response_model=JobStatus)
async def upload_input_file(file: UploadFile = File(...)):
    """
    Upload input CSV/data file to Anaplan (mock)
    This simulates pushing data INTO Anaplan
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    job_id = create_job(file.filename)
    file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update job status
    jobs_db[job_id]["status"] = "ready"
    jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
    jobs_db[job_id]["message"] = f"Input file '{file.filename}' uploaded successfully. Ready for processing."
    jobs_db[job_id]["file_path"] = str(file_path)

    return JobStatus(**jobs_db[job_id])


@app.get("/api/v1/jobs")
def list_jobs():
    """List all jobs"""
    return {"jobs": list(jobs_db.values()), "total": len(jobs_db)}


@app.get("/api/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    """Get status of a specific job"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]


@app.get("/api/v1/download/{job_id}")
def download_input_file(job_id: str):
    """
    Download input file for processing
    Streamlit app will call this to GET the data from "Anaplan"
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_db[job_id]
    file_path = job.get("file_path")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Input file not found")

    # Update status to running
    jobs_db[job_id]["status"] = "running"
    jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
    jobs_db[job_id]["message"] = "Data downloaded by client for processing"

    return FileResponse(
        path=file_path,
        filename=job["input_file"],
        media_type="text/csv"
    )


@app.post("/api/v1/output/{job_id}")
async def push_output(
    job_id: str,
    file: UploadFile = File(...),
    metadata: Optional[str] = None
):
    """
    Push forecast output back to Anaplan (mock)
    Streamlit app will upload the generated output here
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    output_filename = f"{job_id}_output_{file.filename}"
    output_path = OUTPUT_DIR / output_filename

    # Save output file
    with open(output_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update job
    jobs_db[job_id]["status"] = "completed"
    jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
    jobs_db[job_id]["output_file"] = output_filename
    jobs_db[job_id]["output_path"] = str(output_path)
    jobs_db[job_id]["message"] = "Forecast output received and stored successfully"

    if metadata:
        try:
            jobs_db[job_id]["metadata"] = json.loads(metadata)
        except:
            jobs_db[job_id]["metadata"] = {"raw": metadata}

    return {
        "success": True,
        "job_id": job_id,
        "message": "Output uploaded to Anaplan successfully",
        "output_file": output_filename,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/output/{job_id}/download")
def download_output_file(job_id: str):
    """Download the processed output from Anaplan"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_db[job_id]
    output_path = job.get("output_path")

    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        path=output_path,
        filename=job.get("output_file", "output.csv"),
        media_type="text/csv"
    )


@app.delete("/api/v1/jobs/{job_id}")
def delete_job(job_id: str):
    """Delete a job and its files"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_db.pop(job_id)

    # Cleanup files
    for key in ["file_path", "output_path"]:
        path = job.get(key)
        if path and os.path.exists(path):
            os.remove(path)

    return {"success": True, "message": f"Job {job_id} deleted"}


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 Mock Anaplan Server Starting...")
    print("=" * 60)
    print("  📍 URL: http://localhost:8000")
    print("  📖 Docs: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
