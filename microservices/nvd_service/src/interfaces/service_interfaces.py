"""
NVD Service Interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.schemas import JobData, NVDSearchResponse, QueueStatus, DetailedReport, ReportByKeyword


class INVDAPIService(ABC):
    """Interface for NVD API Service"""
    
    @abstractmethod
    async def search_vulnerabilities(
        self, 
        keyword: str, 
        start_index: int = 0, 
        results_per_page: int = 10
    ) -> Dict[str, Any]:
        """Search for vulnerabilities using a keyword"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if NVD API is healthy"""
        pass


class IMongoDBService(ABC):
    """Interface for MongoDB Service"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to MongoDB"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        pass
    
    @abstractmethod
    async def save_job_results(self, jobs_data: List[Dict[str, Any]]) -> None:
        """Save job results to MongoDB"""
        pass
    
    @abstractmethod
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from MongoDB"""
        pass
    
    @abstractmethod
    async def get_reports_by_keywords(self) -> List[ReportByKeyword]:
        """Get vulnerability reports grouped by keywords"""
        pass
    
    @abstractmethod
    async def get_detailed_report_by_keyword(self, keyword: str) -> DetailedReport:
        """Get detailed vulnerability report for a specific keyword"""
        pass


class IQueueService(ABC):
    """Interface for Queue Service"""
    
    @abstractmethod
    def add_job(self, keyword: str, metadata: Dict[str, Any]) -> str:
        """Add a job to the queue"""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job information"""
        pass
    
    @abstractmethod
    def get_all_job_results(self) -> Dict[str, Any]:
        """Get all job results"""
        pass
    
    @abstractmethod
    def peek_queue_status(self) -> QueueStatus:
        """Get queue status"""
        pass
    
    @abstractmethod
    def start_consumer(self) -> Dict[str, str]:
        """Start queue consumer"""
        pass
    
    @abstractmethod
    def stop_consumer(self) -> Dict[str, str]:
        """Stop queue consumer"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if queue service is healthy"""
        pass


class IRiskAnalysisService(ABC):
    """Interface for Risk Analysis Service"""
    
    @abstractmethod
    async def analyze_risk(
        self,
        vulnerabilities: List[Dict[str, Any]],
        asset_criticality: Optional[str] = None,
        threat_landscape: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze risk based on vulnerabilities"""
        pass
