from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"

class ReportType(str, Enum):
    VULNERABILITY_SUMMARY = "vulnerability_summary"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_REPORT = "compliance_report"
    EXECUTIVE_SUMMARY = "executive_summary"

class ReportRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat
    session_id: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    filters: Optional[Dict[str, Any]] = None
    include_charts: bool = True
    include_recommendations: bool = True
    
class ReportResponse(BaseModel):
    report_id: str
    status: str
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    created_at: datetime
    format: ReportFormat
    report_type: ReportType
    
class VulnerabilityData(BaseModel):
    cve_id: str
    severity: str
    score: float
    description: str
    affected_products: List[str]
    published_date: datetime
    business_impact: Optional[str] = None
    
class ReportMetrics(BaseModel):
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    average_score: float
    risk_distribution: Dict[str, int]
