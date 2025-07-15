"""
Risk analysis repository for database operations
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from sqlalchemy.orm import Session
from config.database import get_db, get_mongodb
from models.database_models import RiskAnalysis as RiskAnalysisDB, Asset as AssetDB
from models.risk_models import RiskAnalysisRequest, AssetRiskAnalysis, RiskScore

logger = logging.getLogger(__name__)


class RiskRepository:
    """Repository for risk analysis data operations"""
    
    async def save_analysis(
        self,
        analysis_id: str,
        request: RiskAnalysisRequest,
        asset_analyses: List[AssetRiskAnalysis],
        overall_risk: RiskScore
    ) -> bool:
        """Save risk analysis to database"""
        try:
            # Save to PostgreSQL
            await self._save_to_postgres(analysis_id, request, asset_analyses, overall_risk)
            
            # Save to MongoDB for detailed storage
            await self._save_to_mongodb(analysis_id, request, asset_analyses, overall_risk)
            
            logger.info(f"Risk analysis {analysis_id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analysis {analysis_id}: {e}")
            return False
    
    async def _save_to_postgres(
        self,
        analysis_id: str,
        request: RiskAnalysisRequest,
        asset_analyses: List[AssetRiskAnalysis],
        overall_risk: RiskScore
    ):
        """Save analysis summary to PostgreSQL"""
        db = next(get_db())
        try:
            # Prepare assets data
            assets_data = [
                {
                    "name": asset.asset.name,
                    "type": asset.asset.type.value,
                    "version": asset.asset.version,
                    "vendor": asset.asset.vendor,
                    "risk_score": asset.risk_score.overall_score
                }
                for asset in asset_analyses
            ]
            
            # Create analysis record
            analysis = RiskAnalysisDB(
                analysis_id=analysis_id,
                overall_risk_score=overall_risk.overall_score,
                overall_risk_level=overall_risk.risk_level.value,
                assets_analyzed=assets_data,
                vulnerabilities_found=sum(len(a.vulnerabilities) for a in asset_analyses),
                recommendations=[rec for asset in asset_analyses for rec in asset.recommendations],
                analysis_metadata={  # Changed from 'metadata' to 'analysis_metadata'
                    "analysis_type": request.analysis_type,
                    "nvd_enabled": request.include_nvd,
                    "ml_enabled": request.include_ml_prediction
                }
            )
            
            db.add(analysis)
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def _save_to_mongodb(
        self,
        analysis_id: str,
        request: RiskAnalysisRequest,
        asset_analyses: List[AssetRiskAnalysis],
        overall_risk: RiskScore
    ):
        """Save detailed analysis to MongoDB"""
        mongodb = await get_mongodb()
        if not mongodb:
            return
        
        try:
            # Prepare detailed document
            document = {
                "analysis_id": analysis_id,
                "timestamp": datetime.utcnow(),
                "request": {
                    "analysis_type": request.analysis_type,
                    "include_nvd": request.include_nvd,
                    "include_ml_prediction": request.include_ml_prediction,
                    "assets": [
                        {
                            "name": asset.name,
                            "type": asset.type.value,
                            "version": asset.version,
                            "vendor": asset.vendor,
                            "cpe": asset.cpe
                        }
                        for asset in request.assets
                    ]
                },
                "overall_risk": {
                    "score": overall_risk.overall_score,
                    "level": overall_risk.risk_level.value,
                    "factors": overall_risk.factors
                },
                "asset_analyses": [
                    {
                        "asset": {
                            "name": analysis.asset.name,
                            "type": analysis.asset.type.value,
                            "version": analysis.asset.version,
                            "vendor": analysis.asset.vendor,
                            "cpe": analysis.asset.cpe
                        },
                        "risk_score": {
                            "score": analysis.risk_score.overall_score,
                            "level": analysis.risk_score.risk_level.value,
                            "factors": analysis.risk_score.factors
                        },
                        "vulnerabilities": [
                            {
                                "cve_id": vuln.cve_id,
                                "description": vuln.description,
                                "cvss_score": vuln.cvss_score,
                                "severity": vuln.severity,
                                "published_date": vuln.published_date.isoformat() if vuln.published_date else None,
                                "last_modified": vuln.last_modified.isoformat() if vuln.last_modified else None
                            }
                            for vuln in analysis.vulnerabilities
                        ],
                        "recommendations": analysis.recommendations
                    }
                    for analysis in asset_analyses
                ]
            }
            
            await mongodb.risk_analyses.insert_one(document)
            
        except Exception as e:
            logger.error(f"MongoDB save failed: {e}")
            # Don't raise - PostgreSQL save is more important
    
    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID from MongoDB"""
        try:
            mongodb = await get_mongodb()
            if not mongodb:
                return None
            
            document = await mongodb.risk_analyses.find_one({"analysis_id": analysis_id})
            return document
            
        except Exception as e:
            logger.error(f"Failed to get analysis {analysis_id}: {e}")
            return None
    
    async def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent risk analyses"""
        try:
            db = next(get_db())
            analyses = db.query(RiskAnalysisDB).order_by(
                RiskAnalysisDB.timestamp.desc()
            ).limit(limit).all()
            
            return [
                {
                    "analysis_id": analysis.analysis_id,
                    "timestamp": analysis.timestamp.isoformat(),
                    "overall_risk_score": analysis.overall_risk_score,
                    "overall_risk_level": analysis.overall_risk_level,
                    "assets_count": len(analysis.assets_analyzed),
                    "vulnerabilities_found": analysis.vulnerabilities_found
                }
                for analysis in analyses
            ]
            
        except Exception as e:
            logger.error(f"Failed to get recent analyses: {e}")
            return []
    
    async def get_risk_matrix_data(self) -> Dict[str, Any]:
        """Get risk matrix data for visualization"""
        try:
            db = next(get_db())
            
            # Get risk distribution
            risk_distribution = {}
            analyses = db.query(RiskAnalysisDB).all()
            
            for analysis in analyses:
                level = analysis.overall_risk_level
                risk_distribution[level] = risk_distribution.get(level, 0) + 1
            
            # Get asset type distribution
            asset_type_distribution = {}
            for analysis in analyses:
                for asset in analysis.assets_analyzed:
                    asset_type = asset.get("type", "unknown")
                    if asset_type not in asset_type_distribution:
                        asset_type_distribution[asset_type] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
                    
                    # Map risk score to level for this asset
                    risk_score = asset.get("risk_score", 0)
                    if risk_score >= 8.0:
                        level = "critical"
                    elif risk_score >= 6.0:
                        level = "high"
                    elif risk_score >= 3.0:
                        level = "medium"
                    else:
                        level = "low"
                    
                    asset_type_distribution[asset_type][level] += 1
            
            # Build matrix data
            matrix_data = []
            for asset_type, levels in asset_type_distribution.items():
                for level, count in levels.items():
                    if count > 0:
                        matrix_data.append({
                            "asset_type": asset_type,
                            "risk_level": level,
                            "count": count
                        })
            
            return {
                "matrix": matrix_data,
                "risk_distribution": risk_distribution,
                "total_analyses": len(analyses),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate risk matrix data: {e}")
            return {
                "matrix": [],
                "risk_distribution": {},
                "total_analyses": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
