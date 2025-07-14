import os
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from app.api.schemas import ReportRequest, ReportResponse, ReportFormat, ReportType
from app.services.report_service import ReportService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Dependency to get report service
def get_report_service() -> ReportService:
    return ReportService()

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    report_service: ReportService = Depends(get_report_service)
):
    """Generate a new report"""
    try:
        logger.info(f"Generating report: {request.report_type.value} in {request.format.value} format")
        
        # Generate report
        report_response = await report_service.generate_report(request)
        
        # Schedule cleanup of old reports in background
        background_tasks.add_task(report_service.cleanup_old_reports)
        
        return report_response
        
    except Exception as e:
        logger.error(f"Error in generate_report endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Download a generated report"""
    try:
        report_info = report_service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(status_code=404, detail="Report not found")
        
        file_path = report_service.get_report_file_path(report_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report file not found")
        
        # Determine media type and filename
        if report_info["format"] == ReportFormat.PDF:
            media_type = "application/pdf"
            filename = f"vulnerability_report_{report_id}.pdf"
        elif report_info["format"] == ReportFormat.HTML:
            media_type = "text/html"
            filename = f"vulnerability_report_{report_id}.html"
        else:
            media_type = "application/octet-stream"
            filename = f"report_{report_id}"
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download report")

@router.get("/{report_id}/preview")
async def preview_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Preview an HTML report in the browser"""
    try:
        report_info = report_service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report_info["format"] != ReportFormat.HTML:
            raise HTTPException(status_code=400, detail="Preview only available for HTML reports")
        
        file_path = report_service.get_report_file_path(report_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report file not found")
        
        # Read and return HTML content
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview report")

@router.get("/{report_id}/info")
async def get_report_info(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Get information about a specific report"""
    try:
        report_info = report_service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "report_id": report_id,
            "status": "completed",
            "created_at": report_info["created_at"],
            "format": report_info["format"],
            "report_type": report_info["report_type"],
            "vulnerabilities_count": report_info["vulnerabilities_count"],
            "download_url": f"/api/reports/{report_id}/download",
            "preview_url": f"/api/reports/{report_id}/preview" if report_info["format"] == ReportFormat.HTML else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report info {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get report information")

@router.get("/types")
async def get_report_types():
    """Get available report types and formats"""
    return {
        "report_types": [
            {
                "id": ReportType.VULNERABILITY_SUMMARY,
                "name": "Vulnerability Summary",
                "description": "Comprehensive vulnerability assessment report"
            },
            {
                "id": ReportType.RISK_ASSESSMENT,
                "name": "Risk Assessment",
                "description": "Risk analysis and assessment report"
            },
            {
                "id": ReportType.COMPLIANCE_REPORT,
                "name": "Compliance Report",
                "description": "Compliance and regulatory report"
            },
            {
                "id": ReportType.EXECUTIVE_SUMMARY,
                "name": "Executive Summary",
                "description": "High-level executive summary report"
            }
        ],
        "formats": [
            {
                "id": ReportFormat.PDF,
                "name": "PDF",
                "description": "Portable Document Format for printing and archival"
            },
            {
                "id": ReportFormat.HTML,
                "name": "HTML",
                "description": "Interactive HTML format for web viewing"
            }
        ]
    }

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Delete a generated report"""
    try:
        report_info = report_service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Remove file
        file_path = report_service.get_report_file_path(report_id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from cache
        if report_id in report_service.reports_cache:
            del report_service.reports_cache[report_id]
        
        return {"message": "Report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete report")
