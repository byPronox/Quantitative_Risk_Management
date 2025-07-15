"""
Risk analysis models and schemas
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

try:
    from pydantic import BaseModel, Field
except ImportError:
    print("Warning: Pydantic not installed. Install with: pip install pydantic")
    
    # Fallback base class
    class BaseModel:
        pass
    
    def Field(*args, **kwargs):
        return None


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssetType(str, Enum):
    """Asset type enumeration"""
    SOFTWARE = "software"
    HARDWARE = "hardware"
    NETWORK = "network"
    DATA = "data"


class Asset(BaseModel):
    """Asset model"""
    name: str = Field(..., description="Asset name")
    type: AssetType = Field(..., description="Asset type")
    version: Optional[str] = Field(None, description="Asset version")
    vendor: Optional[str] = Field(None, description="Asset vendor")
    cpe: Optional[str] = Field(None, description="Common Platform Enumeration identifier")


class RiskAnalysisRequest(BaseModel):
    """Risk analysis request model"""
    assets: List[Asset] = Field(..., description="List of assets to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis to perform")
    include_nvd: bool = Field(True, description="Include NVD vulnerability data")
    include_ml_prediction: bool = Field(True, description="Include ML risk prediction")


class VulnerabilityInfo(BaseModel):
    """Vulnerability information model"""
    cve_id: str = Field(..., description="CVE identifier")
    description: str = Field(..., description="Vulnerability description")
    cvss_score: Optional[float] = Field(None, description="CVSS score")
    severity: str = Field(..., description="Vulnerability severity")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    last_modified: Optional[datetime] = Field(None, description="Last modification date")


class RiskScore(BaseModel):
    """Risk score model"""
    overall_score: float = Field(..., description="Overall risk score (0-10)")
    risk_level: RiskLevel = Field(..., description="Calculated risk level")
    factors: Dict[str, float] = Field(default_factory=dict, description="Risk factors breakdown")


class AssetRiskAnalysis(BaseModel):
    """Individual asset risk analysis result"""
    asset: Asset = Field(..., description="Analyzed asset")
    risk_score: RiskScore = Field(..., description="Risk score")
    vulnerabilities: List[VulnerabilityInfo] = Field(default_factory=list, description="Found vulnerabilities")
    recommendations: List[str] = Field(default_factory=list, description="Risk mitigation recommendations")


class RiskAnalysisResponse(BaseModel):
    """Risk analysis response model"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    overall_risk: RiskScore = Field(..., description="Overall risk assessment")
    asset_analyses: List[AssetRiskAnalysis] = Field(..., description="Individual asset analyses")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Analysis summary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
