from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class VulnerabilitySearchRequest(BaseModel):
    """Request schema for vulnerability search"""
    keywords: Optional[str] = Field(None, description="Keywords to search for")
    cve_id: Optional[str] = Field(None, description="Specific CVE ID")
    cpe_name: Optional[str] = Field(None, description="CPE name filter")
    results_per_page: int = Field(default=20, ge=1, le=2000)
    start_index: int = Field(default=0, ge=0)
    pub_start_date: Optional[str] = Field(None, description="Publication start date (YYYY-MM-DD)")
    pub_end_date: Optional[str] = Field(None, description="Publication end date (YYYY-MM-DD)")
    last_mod_start_date: Optional[str] = Field(None, description="Last modified start date (YYYY-MM-DD)")
    last_mod_end_date: Optional[str] = Field(None, description="Last modified end date (YYYY-MM-DD)")


class VulnerabilityMetric(BaseModel):
    """CVSS metrics for a vulnerability"""
    source: str
    type: str
    cvss_data: Dict[str, Any]
    base_score: float
    base_severity: str
    exploitability_score: Optional[float] = None
    impact_score: Optional[float] = None


class VulnerabilityReference(BaseModel):
    """External reference for vulnerability"""
    url: str
    source: Optional[str] = None
    tags: List[str] = []


class VulnerabilityDescription(BaseModel):
    """Description of vulnerability"""
    lang: str
    value: str


class Vulnerability(BaseModel):
    """NVD Vulnerability data model"""
    id: str
    source_identifier: str
    published: datetime
    last_modified: datetime
    vuln_status: str
    descriptions: List[VulnerabilityDescription]
    metrics: Optional[Dict[str, List[VulnerabilityMetric]]] = None
    weaknesses: Optional[List[Dict[str, Any]]] = None
    configurations: Optional[List[Dict[str, Any]]] = None
    references: Optional[List[VulnerabilityReference]] = None
    vendor_comments: Optional[List[Dict[str, Any]]] = None


class VulnerabilitySearchResponse(BaseModel):
    """Response schema for vulnerability search"""
    vulnerabilities: List[Vulnerability]
    total_results: int
    results_per_page: int
    start_index: int
    format: str
    version: str
    timestamp: datetime


class RiskAnalysisRequest(BaseModel):
    """Request schema for risk analysis"""
    vulnerabilities: List[str] = Field(..., description="List of CVE IDs")
    asset_criticality: float = Field(default=1.0, ge=0.0, le=1.0, description="Asset criticality factor")
    threat_landscape: Optional[str] = Field(default="medium", description="Threat landscape level")


class RiskScore(BaseModel):
    """Risk score for a single vulnerability"""
    cve_id: str
    base_score: float
    exploitability: float
    impact: float
    threat_intelligence: float
    asset_criticality: float
    composite_score: float
    risk_level: str  # low, medium, high, critical


class RiskAnalysisResponse(BaseModel):
    """Response schema for risk analysis"""
    overall_risk_score: float
    risk_level: str
    vulnerability_risks: List[RiskScore]
    recommendations: List[str]
    analysis_timestamp: datetime


class QueueJobRequest(BaseModel):
    """Request schema for queuing vulnerability analysis"""
    job_type: str = Field(..., description="Type of job (search, analysis)")
    parameters: Dict[str, Any] = Field(..., description="Job parameters")
    priority: int = Field(default=1, ge=1, le=10, description="Job priority")
    callback_url: Optional[str] = Field(None, description="Callback URL for results")


class QueueJobResponse(BaseModel):
    """Response schema for queued job"""
    job_id: str
    status: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class QueueJobStatus(BaseModel):
    """Status of a queued job"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 to 1.0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ServiceMetrics(BaseModel):
    """Service metrics response"""
    service_name: str
    uptime_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    queue_size: int
    active_jobs: int
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str  # healthy, unhealthy, degraded
    timestamp: datetime
    services: Dict[str, str]  # service_name -> status
    version: str
