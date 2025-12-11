"""
Nmap Controller for Async Scanning
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from config.database import get_db
from models.database_models import NmapJob
from services.nmap_queue_service import NmapQueueService

router = APIRouter()
queue_service = NmapQueueService()

@router.post("/scan/async")
async def start_async_scan(target: str, db: Session = Depends(get_db)):
    """
    Start an asynchronous Nmap scan.
    Returns a job_id to track progress.
    """
    job_id = str(uuid.uuid4())
    
    # Create job record in DB
    job = NmapJob(
        job_id=job_id,
        target=target,
        status="queued"
    )
    db.add(job)
    db.commit()
    
    # Publish to Queue
    success = queue_service.publish_scan_job(job_id, target)
    
    if not success:
        job.status = "failed"
        job.error = "Failed to publish to queue"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to queue scan job")
        
    return {
        "job_id": job_id,
        "target": target,
        "status": "queued",
        "message": "Scan job submitted successfully"
    }

@router.get("/scan/status/{job_id}")
async def get_scan_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status and result of a scan job"""
    job = db.query(NmapJob).filter(NmapJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job.job_id,
        "target": job.target,
        "status": job.status,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "result": job.result,
        "error": job.error
    }

@router.get("/scan/history")
async def get_scan_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get history of Nmap scans"""
    jobs = db.query(NmapJob).order_by(NmapJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs
