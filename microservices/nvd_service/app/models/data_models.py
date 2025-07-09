from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CVSSMetrics:
    """CVSS metrics data class"""
    version: str
    vector_string: str
    attack_vector: str
    attack_complexity: str
    privileges_required: str
    user_interaction: str
    scope: str
    confidentiality_impact: str
    integrity_impact: str
    availability_impact: str
    base_score: float
    base_severity: str
    exploitability_score: Optional[float] = None
    impact_score: Optional[float] = None


@dataclass
class VulnerabilityReference:
    """Vulnerability reference data class"""
    url: str
    source: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class VulnerabilityWeakness:
    """Vulnerability weakness data class"""
    source: str
    type: str
    description: List[Dict[str, str]]


@dataclass
class VulnerabilityConfiguration:
    """Vulnerability configuration data class"""
    nodes: List[Dict[str, Any]]
    operator: Optional[str] = None


@dataclass
class VulnerabilityData:
    """Complete vulnerability data"""
    cve_id: str
    source_identifier: str
    published: datetime
    last_modified: datetime
    vuln_status: str
    descriptions: List[Dict[str, str]]
    cvss_metrics_v2: Optional[CVSSMetrics] = None
    cvss_metrics_v3: Optional[CVSSMetrics] = None
    cvss_metrics_v31: Optional[CVSSMetrics] = None
    weaknesses: List[VulnerabilityWeakness] = None
    configurations: List[VulnerabilityConfiguration] = None
    references: List[VulnerabilityReference] = None
    vendor_comments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.weaknesses is None:
            self.weaknesses = []
        if self.configurations is None:
            self.configurations = []
        if self.references is None:
            self.references = []
        if self.vendor_comments is None:
            self.vendor_comments = []
    
    @property
    def primary_cvss_score(self) -> Optional[float]:
        """Get primary CVSS score (preferring v3.1 > v3.0 > v2)"""
        if self.cvss_metrics_v31:
            return self.cvss_metrics_v31.base_score
        elif self.cvss_metrics_v3:
            return self.cvss_metrics_v3.base_score
        elif self.cvss_metrics_v2:
            return self.cvss_metrics_v2.base_score
        return None
    
    @property
    def primary_cvss_severity(self) -> Optional[str]:
        """Get primary CVSS severity"""
        if self.cvss_metrics_v31:
            return self.cvss_metrics_v31.base_severity
        elif self.cvss_metrics_v3:
            return self.cvss_metrics_v3.base_severity
        elif self.cvss_metrics_v2:
            return self.cvss_metrics_v2.base_severity
        return None


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    cve_id: str
    base_score: float
    exploitability_score: float
    impact_score: float
    threat_intelligence_score: float
    asset_criticality_factor: float
    composite_risk_score: float
    risk_level: RiskLevel
    confidence: float
    recommendations: List[str]
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class QueueJob:
    """Queue job data class"""
    job_id: str
    job_type: str
    parameters: Dict[str, Any]
    status: JobStatus
    priority: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    callback_url: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    @property
    def is_active(self) -> bool:
        """Check if job is in an active state"""
        return self.status in [JobStatus.PENDING, JobStatus.PROCESSING]
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete (success or failure)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    status: str  # healthy, unhealthy, degraded
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    dependencies: Dict[str, str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}


@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    service_name: str
    uptime_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    queue_size: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100
