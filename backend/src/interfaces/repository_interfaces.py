"""
Repository interfaces (abstract base classes)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from models.risk_models import RiskAnalysisRequest, AssetRiskAnalysis, RiskScore


class IRiskRepository(ABC):
    """Interface for risk repository operations"""
    
    @abstractmethod
    async def save_analysis(
        self,
        analysis_id: str,
        request: RiskAnalysisRequest,
        asset_analyses: List[AssetRiskAnalysis],
        overall_risk: RiskScore
    ) -> bool:
        """Save risk analysis to storage"""
        pass
    
    @abstractmethod
    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID"""
        pass
    
    @abstractmethod
    async def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent risk analyses"""
        pass
    
    @abstractmethod
    async def get_risk_matrix_data(self) -> Dict[str, Any]:
        """Get risk matrix data for visualization"""
        pass


class INVDService(ABC):
    """Interface for NVD service operations"""
    
    @abstractmethod
    async def get_vulnerabilities(
        self,
        cpe_name: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get vulnerabilities from NVD"""
        pass
    
    @abstractmethod
    async def search_cpe(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for CPE entries"""
        pass
    
    @abstractmethod
    async def analyze_software_list(self, software_list: List[str]) -> Dict[str, Any]:
        """Analyze software list for vulnerabilities"""
        pass
