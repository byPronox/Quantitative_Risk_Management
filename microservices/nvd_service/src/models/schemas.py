"""
NVD Service Data Models
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class CVEMetrics(BaseModel):
    """CVE Metrics Model"""
    cvssMetricV31: Optional[List[Dict[str, Any]]] = []
    cvssMetricV2: Optional[List[Dict[str, Any]]] = []


class CVEDescription(BaseModel):
    """CVE Description Model"""
    lang: str
    value: str


class CVEReference(BaseModel):
    """CVE Reference Model"""
    url: str
    source: str
    tags: Optional[List[str]] = []


class CVEWeakness(BaseModel):
    """CVE Weakness Model"""
    source: str
    type: str
    description: List[Dict[str, str]]


class CVEConfiguration(BaseModel):
    """CVE Configuration Model"""
    nodes: List[Dict[str, Any]]


class CVEData(BaseModel):
    """CVE Data Model"""
    id: str
    sourceIdentifier: str
    published: str
    lastModified: str
    vulnStatus: str
    cveTags: List[str] = []
    descriptions: List[CVEDescription]
    metrics: CVEMetrics
    weaknesses: List[CVEWeakness] = []
    configurations: List[CVEConfiguration] = []
    references: List[CVEReference] = []
    vendorComments: List[Dict[str, Any]] = []


class Vulnerability(BaseModel):
    """Vulnerability Model"""
    cve: CVEData


class JobData(BaseModel):
    """Job Data Model"""
    job_id: str
    keyword: str
    status: str = "queued"  # queued, processing, completed, failed
    total_results: int = 0
    processed_at: Optional[float] = None
    processed_via: Optional[str] = None
    vulnerabilities: List[Vulnerability] = []
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}


class NVDSearchRequest(BaseModel):
    """NVD Search Request Model"""
    keyword: str
    startIndex: int = 0
    resultsPerPage: int = 10
    maxResults: int = 100


class NVDSearchResponse(BaseModel):
    """NVD Search Response Model"""
    success: bool
    totalResults: int = 0
    vulnerabilities: List[Vulnerability] = []
    message: Optional[str] = None
    error: Optional[str] = None


class QueueJobRequest(BaseModel):
    """Queue Job Request Model"""
    keyword: str
    metadata: Optional[Dict[str, Any]] = {}


class QueueJobResponse(BaseModel):
    """Queue Job Response Model"""
    job_id: str
    keyword: str
    status: str
    message: str


class QueueStatus(BaseModel):
    """Queue Status Model"""
    queue_size: int
    pending: int
    processing: int
    completed: int
    queue_name: str
    status: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health Response Model"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str


class ServiceMetrics(BaseModel):
    """Service Metrics Model"""
    service_name: str
    uptime_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    queue_size: int
    active_jobs: int
    timestamp: datetime


class ReportByKeyword(BaseModel):
    """Report by Keyword Model"""
    keyword: str
    total_jobs: int
    total_vulnerabilities: int
    latest_analysis: Optional[str] = None
    jobs: List[Dict[str, Any]] = []


class DetailedReport(BaseModel):
    """Detailed Report Model"""
    success: bool
    keyword: str
    total_jobs: int
    total_vulnerabilities: int
    severity_distribution: Dict[str, int]
    vulnerabilities_by_year: Dict[str, int]
    jobs: List[JobData]
    vulnerabilities: List[Vulnerability]
