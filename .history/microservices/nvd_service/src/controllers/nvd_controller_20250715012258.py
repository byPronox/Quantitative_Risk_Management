"""
NVD Service API Controllers
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# Import existing services for now, we'll migrate them gradually
from app.services.nvd_service import NVDService
from app.services.queue_service import QueueService

# Import refactored services
from ..services.mongodb_service import MongoDBService

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances
nvd_service = NVDService()
queue_service = QueueService()
mongodb_service = MongoDBService()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "NVD Microservice",
            "version": "1.0.0",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/queue/status")
async def get_queue_status():
    """Get current queue status"""
    try:
        status = queue_service.peek_queue_status()
        return status
    except Exception as e:
        logger.error("Error getting queue status: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/add")
async def add_to_queue(request: Dict[str, Any]):
    """Add keyword to analysis queue"""
    try:
        keyword = request.get("keyword")
        if not keyword:
            raise HTTPException(status_code=400, detail="Keyword is required")
        
        job_id = queue_service.add_job(keyword, request.get("metadata", {}))
        return {
            "message": f"Keyword '{keyword}' added to analysis queue",
            "job_id": job_id,
            "keyword": keyword,
            "status": "queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add to queue: {str(e)}")


@router.post("/consumer/start")
async def start_consumer():
    """Start the queue consumer"""
    try:
        result = queue_service.start_consumer()
        return result
    except Exception as e:
        logger.error("Error starting consumer: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consumer/stop")
async def stop_consumer():
    """Stop the queue consumer"""
    try:
        result = queue_service.stop_consumer()
        return result
    except Exception as e:
        logger.error("Error stopping consumer: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LEGACY ENDPOINTS (for backward compatibility)
# =============================================================================

@router.get("/results/all")
async def get_all_results_legacy():
    """Get all NVD analysis results (legacy endpoint)"""
    try:
        results = queue_service.get_all_job_results()
        return results
    except Exception as e:
        logger.error("Error getting all results: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MONGODB ENDPOINTS (New refactored endpoints)
# =============================================================================

@router.get("/mongodb/results/all")
async def get_all_mongodb_results():
    """Get all NVD analysis results from MongoDB"""
    try:
        results = await mongodb_service.get_all_jobs()
        return {
            "success": True,
            "total_jobs": len(results),
            "jobs": results
        }
    except Exception as e:
        logger.error("Error getting all MongoDB results: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mongodb/results/{keyword}")
async def get_mongodb_results_by_keyword(keyword: str):
    """Get NVD analysis results by keyword from MongoDB"""
    try:
        results = await mongodb_service.get_detailed_report_by_keyword(keyword)
        return results
    except Exception as e:
        logger.error("Error getting MongoDB results for keyword %s: %s", keyword, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mongodb/reports/keywords")
async def get_mongodb_reports_by_keywords():
    """Get vulnerability reports grouped by keywords from MongoDB"""
    try:
        reports = await mongodb_service.get_reports_by_keywords()
        return {
            "success": True,
            "keywords": reports
        }
    except Exception as e:
        logger.error("Error getting MongoDB reports by keywords: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mongodb/reports/detailed/{keyword}")
async def get_mongodb_detailed_report(keyword: str):
    """Get detailed vulnerability report for a specific keyword from MongoDB"""
    try:
        report = await mongodb_service.get_detailed_report_by_keyword(keyword)
        return report
    except Exception as e:
        logger.error("Error getting MongoDB detailed report for %s: %s", keyword, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mongodb/analyze")
async def analyze_cves_with_mongodb(
    keywords: List[str],
    max_results: int = Query(default=100, ge=1, le=1000)
):
    """Analyze CVEs for given keywords and save to MongoDB"""
    try:
        # For now, this is a placeholder - we'll need to implement the actual analysis
        # This would typically interface with the NVD API and then save to MongoDB
        return {
            "success": True,
            "message": f"Analysis requested for {len(keywords)} keywords",
            "keywords": keywords,
            "max_results": max_results
        }
    except Exception as e:
        logger.error("Error analyzing CVEs with MongoDB: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mongodb/health")
async def check_mongodb_health():
    """Check MongoDB connection health"""
    try:
        await mongodb_service.connect()
        await mongodb_service.disconnect()
        return {
            "success": True,
            "message": "MongoDB connection healthy",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error("MongoDB health check failed: %s", str(e))
        return {
            "success": False,
            "message": f"MongoDB connection failed: {str(e)}",
            "timestamp": datetime.utcnow()
        }
