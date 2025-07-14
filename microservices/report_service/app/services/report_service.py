import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from app.api.schemas import ReportRequest, ReportResponse, ReportFormat, ReportType
from app.services.data_service import DataService
from app.services.pdf_generator import PDFReportGenerator
from app.services.html_generator import HTMLReportGenerator
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """Main service for generating reports"""
    
    def __init__(self):
        self.data_service = DataService()
        self.pdf_generator = PDFReportGenerator()
        self.html_generator = HTMLReportGenerator()
        self.reports_cache = {}  # Simple in-memory cache for generated reports
    
    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        """Generate a report based on the request parameters"""
        try:
            report_id = str(uuid.uuid4())
            logger.info(f"Starting report generation: {report_id}")
            
            # Fetch vulnerability data
            vulnerabilities = await self.data_service.get_vulnerability_data(
                session_id=request.session_id,
                date_range=request.date_range,
                filters=request.filters
            )
            
            if not vulnerabilities:
                logger.warning("No vulnerability data found for report generation")
                return ReportResponse(
                    report_id=report_id,
                    status="error",
                    created_at=datetime.now(),
                    format=request.format,
                    report_type=request.report_type
                )
            
            # Calculate metrics
            metrics = self.data_service.calculate_metrics(vulnerabilities)
            
            # Get session info if session_id is provided
            session_info = {}
            if request.session_id:
                session_info = await self.data_service.get_session_info(request.session_id)
            
            # Generate report based on format
            filename = None
            
            if request.format == ReportFormat.PDF:
                if request.report_type == ReportType.VULNERABILITY_SUMMARY:
                    filename = self.pdf_generator.generate_vulnerability_summary(
                        vulnerabilities, metrics, session_info
                    )
                # Add other report types as needed
                
            elif request.format == ReportFormat.HTML:
                if request.report_type == ReportType.VULNERABILITY_SUMMARY:
                    filename = self.html_generator.generate_vulnerability_summary(
                        vulnerabilities, metrics, session_info
                    )
                # Add other report types as needed
            
            if filename:
                # Store report info in cache
                self.reports_cache[report_id] = {
                    "filename": filename,
                    "created_at": datetime.now(),
                    "format": request.format,
                    "report_type": request.report_type,
                    "vulnerabilities_count": len(vulnerabilities)
                }
                
                return ReportResponse(
                    report_id=report_id,
                    status="completed",
                    download_url=f"/api/reports/{report_id}/download",
                    preview_url=f"/api/reports/{report_id}/preview" if request.format == ReportFormat.HTML else None,
                    created_at=datetime.now(),
                    format=request.format,
                    report_type=request.report_type
                )
            else:
                return ReportResponse(
                    report_id=report_id,
                    status="error",
                    created_at=datetime.now(),
                    format=request.format,
                    report_type=request.report_type
                )
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ReportResponse(
                report_id=str(uuid.uuid4()),
                status="error",
                created_at=datetime.now(),
                format=request.format,
                report_type=request.report_type
            )
    
    def get_report_info(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a generated report"""
        return self.reports_cache.get(report_id)
    
    def get_report_file_path(self, report_id: str) -> Optional[str]:
        """Get the file path for a generated report"""
        report_info = self.reports_cache.get(report_id)
        if report_info:
            if report_info["format"] == ReportFormat.PDF:
                return os.path.join(self.pdf_generator.temp_dir, report_info["filename"])
            elif report_info["format"] == ReportFormat.HTML:
                return os.path.join(self.html_generator.temp_dir, report_info["filename"])
        return None
    
    def cleanup_old_reports(self, max_age_hours: int = 24):
        """Clean up old report files and cache entries"""
        current_time = datetime.now()
        reports_to_remove = []
        
        for report_id, report_info in self.reports_cache.items():
            age = current_time - report_info["created_at"]
            if age.total_seconds() > max_age_hours * 3600:
                # Remove file
                file_path = self.get_report_file_path(report_id)
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old report file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing report file {file_path}: {e}")
                
                reports_to_remove.append(report_id)
        
        # Remove from cache
        for report_id in reports_to_remove:
            del self.reports_cache[report_id]
        
        if reports_to_remove:
            logger.info(f"Cleaned up {len(reports_to_remove)} old reports")
