"""
Enhanced Risk Analysis Controller with Nmap Integration and Risk Rubric
"""
import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import asyncio

from config.settings import settings
from services.enhanced_risk_service import EnhancedRiskAnalysisService, RiskMitigationStrategy, VulnerabilitySeverity

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for enhanced risk analysis
class NmapScanRequest(BaseModel):
    ip: str = Field(..., description="IP address or hostname to scan")
    include_vulnerability_analysis: bool = Field(True, description="Include detailed vulnerability analysis")
    include_risk_rubric: bool = Field(True, description="Include AVOID/MITIGATE/TRANSFER/ACCEPT recommendations")

class RiskRubricResponse(BaseModel):
    target: str
    scan_timestamp: str
    overall_risk_level: str
    services_analysis: List[Dict[str, Any]]
    vulnerabilities_analysis: List[Dict[str, Any]]
    risk_recommendations: List[Dict[str, Any]]
    mitigation_strategies: Dict[str, Any]
    technical_summary: str

class ServiceRiskAnalysis(BaseModel):
    port: str
    service_name: str
    risk_level: str
    mitigation_strategy: str
    technical_details: str
    recommended_actions: List[str]

class VulnerabilityRiskAnalysis(BaseModel):
    vulnerability_id: str
    severity: str
    mitigation_strategy: str
    technical_details: str
    recommended_actions: List[str]

# Initialize enhanced risk analysis service
enhanced_risk_service = EnhancedRiskAnalysisService()

async def get_nmap_service_client():
    """Get HTTP client for nmap service"""
    return httpx.AsyncClient(
        base_url="http://nmap-scanner-service:8004",
        timeout=httpx.Timeout(300.0)  # 5 minutes timeout
    )

@router.post("/risk/nmap-analysis", response_model=RiskRubricResponse)
async def analyze_nmap_with_risk_rubric(request: NmapScanRequest):
    """
    Perform comprehensive nmap scan with detailed risk analysis and mitigation strategies
    
    This endpoint:
    1. Executes nmap vulnerability scan
    2. Analyzes each service and vulnerability
    3. Applies AVOID/MITIGATE/TRANSFER/ACCEPT rubric
    4. Provides specific technical recommendations
    """
    logger.info(f"Starting comprehensive risk analysis for target: {request.ip}")
    
    try:
        # Step 1: Execute nmap scan
        async with await get_nmap_service_client() as client:
            nmap_response = await client.post(
                "/api/v1/scan",
                json={"ip": request.ip}
            )
            
            if nmap_response.status_code != 200:
                error_data = nmap_response.json()
                logger.error(f"Nmap scan failed for {request.ip}: {error_data}")
                raise HTTPException(
                    status_code=nmap_response.status_code,
                    detail=f"Nmap scan failed: {error_data.get('error', 'Unknown error')}"
                )
            
            nmap_data = nmap_response.json()
            logger.info(f"Nmap scan completed successfully for {request.ip}")
        
        # Step 2: Analyze results with enhanced risk service
        if request.include_risk_rubric:
            risk_analysis = enhanced_risk_service.analyze_nmap_results(nmap_data["data"])
        else:
            # Basic analysis without rubric
            risk_analysis = {
                "target": request.ip,
                "scan_timestamp": nmap_data.get("timestamp", ""),
                "services": [],
                "vulnerabilities": [],
                "risk_assessment": {"overall_level": "UNKNOWN"},
                "recommendations": []
            }
        
        # Step 3: Format response with detailed technical information
        response_data = {
            "target": request.ip,
            "scan_timestamp": risk_analysis["scan_timestamp"],
            "overall_risk_level": risk_analysis["risk_assessment"]["overall_level"],
            "services_analysis": [],
            "vulnerabilities_analysis": [],
            "risk_recommendations": risk_analysis["recommendations"],
            "mitigation_strategies": _get_mitigation_strategies_summary(risk_analysis),
            "technical_summary": _generate_technical_summary(risk_analysis)
        }
        
        # Format services analysis
        for service in risk_analysis["services"]:
            service_analysis = {
                "port": service["port"],
                "protocol": service["protocol"],
                "service_name": service["service_name"],
                "product": service["product"],
                "version": service["version"],
                "risk_level": service["risk_level"].value if hasattr(service["risk_level"], 'value') else str(service["risk_level"]),
                "risk_score": service["risk_score"],
                "mitigation_strategy": service["mitigation_strategy"]["description"],
                "technical_details": service["technical_details"],
                "recommended_actions": service["mitigation_strategy"]["actions"],
                "strategy_rationale": service["mitigation_strategy"]["technical_details"]
            }
            response_data["services_analysis"].append(service_analysis)
        
        # Format vulnerabilities analysis
        for vuln in risk_analysis["vulnerabilities"]:
            vuln_analysis = {
                "vulnerability_id": vuln["id"],
                "severity": vuln["severity"].value if hasattr(vuln["severity"], 'value') else str(vuln["severity"]),
                "output": vuln["output"],
                "mitigation_strategy": vuln["mitigation_strategy"]["description"],
                "technical_details": vuln["technical_details"],
                "recommended_actions": vuln["mitigation_strategy"]["actions"],
                "strategy_rationale": vuln["mitigation_strategy"]["technical_details"]
            }
            response_data["vulnerabilities_analysis"].append(vuln_analysis)
        
        logger.info(f"Risk analysis completed for {request.ip} - Overall risk: {response_data['overall_risk_level']}")
        return RiskRubricResponse(**response_data)
        
    except httpx.TimeoutException:
        logger.error(f"Nmap scan timeout for {request.ip}")
        raise HTTPException(
            status_code=408,
            detail={
                "error": "Scan timeout",
                "details": "Nmap scan exceeded 5 minute timeout",
                "target": request.ip,
                "recommendation": "Try scanning a smaller target or check network connectivity"
            }
        )
    except httpx.ConnectError:
        logger.error("Cannot connect to nmap scanner service")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "details": "Nmap scanner service is not available",
                "recommendation": "Check if nmap-scanner-service is running"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during risk analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e),
                "recommendation": "Check service logs for detailed error information"
            }
        )

@router.get("/risk/mitigation-strategies")
async def get_mitigation_strategies():
    """
    Get detailed information about available mitigation strategies
    """
    strategies_info = {
        "AVOID": {
            "description": "Eliminar o aislar completamente el activo",
            "when_to_use": [
                "Vulnerabilidades críticas (RCE, Authentication bypass)",
                "Riesgo inaceptable de compromiso total",
                "Costo de mitigación excede el valor del activo"
            ],
            "examples": [
                "Desconectar servicio de la red",
                "Aislar en VLAN separada",
                "Reemplazar hardware/software completamente"
            ]
        },
        "MITIGATE": {
            "description": "Aplicar parches, cerrar puertos, endurecer configuraciones",
            "when_to_use": [
                "Parches de seguridad disponibles",
                "Sistema crítico para operaciones",
                "Vulnerabilidades con mitigación conocida"
            ],
            "examples": [
                "Aplicar parches de seguridad",
                "Implementar WAF/IPS",
                "Endurecer configuraciones",
                "Implementar autenticación multifactor"
            ]
        },
        "TRANSFER": {
            "description": "Externalizar el riesgo mediante seguros o servicios especializados",
            "when_to_use": [
                "Sistema no crítico",
                "Recursos internos limitados",
                "Servicios legacy complejos"
            ],
            "examples": [
                "Contratar seguro de ciberseguridad",
                "Externalizar a MSSP",
                "Implementar SOC-as-a-Service"
            ]
        },
        "ACCEPT": {
            "description": "Documentar y monitorear riesgos de bajo impacto",
            "when_to_use": [
                "Riesgo bajo impacto de negocio",
                "Costo de mitigación alto",
                "Vulnerabilidades informativas"
            ],
            "examples": [
                "Documentar en registro de riesgos",
                "Implementar monitoreo continuo",
                "Revisar periódicamente"
            ]
        }
    }
    
    return {
        "strategies": strategies_info,
        "decision_framework": {
            "critical_vulnerabilities": "AVOID or MITIGATE",
            "high_vulnerabilities": "MITIGATE or TRANSFER",
            "medium_vulnerabilities": "MITIGATE or ACCEPT",
            "low_vulnerabilities": "ACCEPT or MITIGATE"
        },
        "technical_guidance": "Each strategy includes specific technical actions and rationale based on vulnerability type and business context"
    }

@router.post("/risk/analyze-service")
async def analyze_specific_service(service_data: Dict[str, Any]):
    """
    Analyze a specific service for risk without full nmap scan
    """
    try:
        # Create mock nmap data structure for single service
        mock_nmap_data = {
            "ip": service_data.get("ip", "unknown"),
            "os": "Unknown",
            "status": "up",
            "services": [service_data],
            "vulnerabilities": []
        }
        
        # Analyze with enhanced risk service
        analysis = enhanced_risk_service.analyze_nmap_results(mock_nmap_data)
        
        # Return focused analysis for the service
        if analysis["services"]:
            service_analysis = analysis["services"][0]
            return {
                "service": service_analysis,
                "risk_assessment": analysis["risk_assessment"],
                "recommendations": analysis["recommendations"]
            }
        else:
            raise HTTPException(status_code=400, detail="No service data provided")
            
    except Exception as e:
        logger.error(f"Service analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service analysis failed: {str(e)}")

def _get_mitigation_strategies_summary(risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of mitigation strategies used"""
    strategies_used = set()
    strategy_counts = {}
    
    # Count strategies from services
    for service in risk_analysis["services"]:
        strategy = service["mitigation_strategy"]["description"]
        strategies_used.add(strategy)
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    # Count strategies from vulnerabilities
    for vuln in risk_analysis["vulnerabilities"]:
        strategy = vuln["mitigation_strategy"]["description"]
        strategies_used.add(strategy)
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    return {
        "strategies_applied": list(strategies_used),
        "strategy_distribution": strategy_counts,
        "total_recommendations": len(risk_analysis["recommendations"])
    }

def _generate_technical_summary(risk_analysis: Dict[str, Any]) -> str:
    """Generate technical summary of the analysis"""
    summary_parts = []
    
    # Overall risk summary
    overall_level = risk_analysis["risk_assessment"]["overall_level"]
    total_services = len(risk_analysis["services"])
    total_vulnerabilities = len(risk_analysis["vulnerabilities"])
    
    summary_parts.append(f"Análisis de riesgo completado para {risk_analysis['target']}.")
    summary_parts.append(f"Nivel de riesgo general: {overall_level}.")
    summary_parts.append(f"Servicios analizados: {total_services}, Vulnerabilidades encontradas: {total_vulnerabilities}.")
    
    # Critical findings
    critical_services = [s for s in risk_analysis["services"] if s["risk_level"] == VulnerabilitySeverity.CRITICAL]
    if critical_services:
        summary_parts.append(f"⚠️ SERVICIOS CRÍTICOS DETECTADOS: {len(critical_services)} servicios requieren acción inmediata.")
    
    # High risk findings
    high_risk_services = [s for s in risk_analysis["services"] if s["risk_level"] == VulnerabilitySeverity.HIGH]
    if high_risk_services:
        summary_parts.append(f"🔴 SERVICIOS DE ALTO RIESGO: {len(high_risk_services)} servicios requieren atención prioritaria.")
    
    # Recommendations summary
    immediate_actions = [r for r in risk_analysis["recommendations"] if r.get("priority") == "IMMEDIATE"]
    if immediate_actions:
        summary_parts.append(f"🚨 ACCIONES INMEDIATAS REQUERIDAS: {len(immediate_actions)} recomendaciones críticas.")
    
    return " ".join(summary_parts)

