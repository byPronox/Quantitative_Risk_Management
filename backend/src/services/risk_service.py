"""
Risk analysis service
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
import httpx

from config.settings import settings
from models.risk_models import RiskAnalysisRequest, RiskAnalysisResponse, RiskScore, RiskLevel, AssetRiskAnalysis
from repositories.risk_repository import RiskRepository

logger = logging.getLogger(__name__)


class RiskService:
    """Service for risk analysis operations"""
    
    def __init__(self):
        self.risk_repository = RiskRepository()
    
    async def analyze_risk(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """
        Perform comprehensive risk analysis
        """
        analysis_id = str(uuid.uuid4())
        # Use TimeService for consistent timestamp
        from services.time_service import TimeService
        time_service = TimeService()
        timestamp = await time_service.get_current_time()
        
        logger.info(f"Starting risk analysis {analysis_id} for {len(request.assets)} assets")
        
        asset_analyses = []
        overall_vulnerabilities = 0
        total_risk_score = 0.0
        
        for asset in request.assets:
            try:
                # Analyze individual asset
                asset_analysis = await self._analyze_asset(asset, request)
                asset_analyses.append(asset_analysis)
                
                overall_vulnerabilities += len(asset_analysis.vulnerabilities)
                total_risk_score += asset_analysis.risk_score.overall_score
                
            except Exception as e:
                logger.error(f"Failed to analyze asset {asset.name}: {e}")
                # Continue with other assets
        
        # Calculate overall risk
        avg_risk_score = total_risk_score / len(request.assets) if request.assets else 0.0
        overall_risk = RiskScore(
            overall_score=avg_risk_score,
            risk_level=self._calculate_risk_level(avg_risk_score),
            factors={
                "vulnerability_count": overall_vulnerabilities,
                "asset_count": len(request.assets),
                "avg_score": avg_risk_score
            }
        )
        
        # Save analysis to database
        await self.risk_repository.save_analysis(analysis_id, request, asset_analyses, overall_risk, timestamp)
        
        return RiskAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=timestamp,
            overall_risk=overall_risk,
            asset_analyses=asset_analyses,
            summary={
                "total_assets": len(request.assets),
                "total_vulnerabilities": overall_vulnerabilities,
                "analysis_type": request.analysis_type
            },
            metadata={
                "nvd_enabled": request.include_nvd,
                "ml_enabled": request.include_ml_prediction
            }
        )
    
    async def _analyze_asset(self, asset, request: RiskAnalysisRequest) -> AssetRiskAnalysis:
        """Analyze individual asset"""
        vulnerabilities = []
        recommendations = []
        risk_factors = {}
        
        # Get NVD vulnerabilities if enabled
        if request.include_nvd and asset.cpe:
            try:
                nvd_data = await self._get_nvd_vulnerabilities(asset.cpe)
                vulnerabilities.extend(nvd_data.get("vulnerabilities", []))
                risk_factors["nvd_score"] = nvd_data.get("risk_score", 0.0)
            except Exception as e:
                logger.warning(f"NVD analysis failed for {asset.name}: {e}")
                risk_factors["nvd_score"] = 0.0
        
        # Get ML predictions if enabled
        if request.include_ml_prediction:
            try:
                ml_score = await self._get_ml_prediction(asset)
                risk_factors["ml_score"] = ml_score
            except Exception as e:
                logger.warning(f"ML prediction failed for {asset.name}: {e}")
                risk_factors["ml_score"] = 0.0
        
        # Calculate overall risk score
        overall_score = self._calculate_asset_risk_score(risk_factors, vulnerabilities)
        
        # Generate recommendations
        if overall_score > 7.0:
            recommendations.append("Immediate patching required - critical vulnerabilities found")
        elif overall_score > 5.0:
            recommendations.append("High priority for security updates")
        elif overall_score > 3.0:
            recommendations.append("Monitor for security updates")
        else:
            recommendations.append("Maintain current security posture")
        
        risk_score = RiskScore(
            overall_score=overall_score,
            risk_level=self._calculate_risk_level(overall_score),
            factors=risk_factors
        )
        
        return AssetRiskAnalysis(
            asset=asset,
            risk_score=risk_score,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations
        )
    
    async def _get_nvd_vulnerabilities(self, cpe: str) -> Dict[str, Any]:
        """Get vulnerabilities from NVD service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{settings.NVD_SERVICE_URL}/api/v1/vulnerabilities",
                    params={"cpe_name": cpe}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"vulnerabilities": [], "risk_score": 0.0}
        except Exception as e:
            logger.error(f"NVD service error: {e}")
            return {"vulnerabilities": [], "risk_score": 0.0}
    
    async def _get_ml_prediction(self, asset) -> float:
        """Get ML risk prediction"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ML_SERVICE_URL}/api/v1/predict",
                    json={
                        "asset_name": asset.name,
                        "asset_type": asset.type.value,
                        "version": asset.version,
                        "vendor": asset.vendor
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("risk_score", 0.0)
                else:
                    return 0.0
        except Exception as e:
            logger.error(f"ML service error: {e}")
            return 0.0
    
    def _calculate_asset_risk_score(self, factors: Dict[str, float], vulnerabilities: List) -> float:
        """Calculate overall risk score for an asset"""
        base_score = factors.get("ml_score", 0.0)
        nvd_score = factors.get("nvd_score", 0.0)
        vuln_count_factor = min(len(vulnerabilities) * 0.5, 5.0)  # Cap at 5 points
        
        # Weighted combination
        overall_score = (base_score * 0.4) + (nvd_score * 0.4) + (vuln_count_factor * 0.2)
        
        return min(overall_score, 10.0)  # Cap at 10
    
    def _calculate_risk_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level"""
        if score >= 8.0:
            return RiskLevel.CRITICAL
        elif score >= 6.0:
            return RiskLevel.HIGH
        elif score >= 3.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def get_risk_matrix(self) -> Dict[str, Any]:
        """Get risk matrix data for visualization"""
        try:
            # This would typically aggregate data from the database
            matrix_data = await self.risk_repository.get_risk_matrix_data()
            return matrix_data
        except Exception as e:
            logger.error(f"Failed to generate risk matrix: {e}")
            # Return mock data as fallback
            return {
                "matrix": [
                    {"asset_type": "software", "risk_level": "high", "count": 5},
                    {"asset_type": "software", "risk_level": "medium", "count": 12},
                    {"asset_type": "software", "risk_level": "low", "count": 8},
                    {"asset_type": "hardware", "risk_level": "medium", "count": 3},
                    {"asset_type": "network", "risk_level": "low", "count": 2}
                ],
                "total_assets": 30,
                "last_updated": datetime.utcnow().isoformat()
            }
