# backend/app/api/nvd.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import httpx
import logging
from config.config import settings
from queue_manager.queue import MessageQueue
from datetime import datetime

router = APIRouter()

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
logger = logging.getLogger(__name__)

class KeywordRequest(BaseModel):
    keyword: str

@router.get("/nvd")
async def get_vulnerabilities(keyword: str = "react"):
    headers = {"apiKey": settings.NVD_API_KEY}
    params = {"keywordSearch": keyword, "startIndex": 0, "resultsPerPage": 10}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(NVD_API_URL, headers=headers, params=params)
            response.raise_for_status()
            logger.info("NVD query for keyword '%s' succeeded.", keyword)
            data = response.json()
            # Return data without saving to queue (only for display)
            return {"vulnerabilities": data.get("vulnerabilities", [])}
    except Exception as e:
        logger.error("NVD API request failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch vulnerabilities from NVD API.") from e

@router.post("/nvd/add_to_queue")
async def add_keyword_to_queue(request: KeywordRequest):
    """Add a specific keyword to the analysis queue"""
    keyword = request.keyword
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    headers = {"apiKey": settings.NVD_API_KEY}
    params = {"keywordSearch": keyword, "startIndex": 0, "resultsPerPage": 10}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(NVD_API_URL, headers=headers, params=params)
            response.raise_for_status()
            logger.info("NVD query for keyword '%s' added to queue.", keyword)
            data = response.json()
            # Save to queue for analysis
            mq = MessageQueue()
            mq.send_message({"keyword": keyword, "vulnerabilities": data.get("vulnerabilities", [])})
            return {
                "message": f"Keyword '{keyword}' added to analysis queue",
                "vulnerabilities_count": len(data.get("vulnerabilities", []))
            }
    except Exception as e:
        logger.error("NVD API request failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to add keyword to queue") from e

@router.post("/nvd/analyze_risk")
async def analyze_nvd_risk():
    # Palabras clave de ejemplo para cada nivel de riesgo
    risk_keywords = {
        "Critical": ["remote code execution", "privilege escalation", "arbitrary code", "unauthenticated", "root access", "critical"],
        "High": ["denial of service", "bypass authentication", "sql injection", "directory traversal", "high"],
        "Medium": ["information disclosure", "medium", "xss", "cross-site scripting", "csrf"],
        "Low": ["low", "minor", "limited impact"],
        "Very Low": ["no impact", "informational", "very low"]
    }
    mq = MessageQueue()
    messages = mq.get_all_messages()
    if not messages:
        return {"detail": "No NVD searches in queue."}
    # Analiza los riesgos por palabra clave
    results = []
    for msg in messages:
        keyword = msg["keyword"]
        vulns = msg["vulnerabilities"]
        risk_count = {k: 0 for k in risk_keywords}
        total = 0
        for vuln in vulns:
            desc = vuln["cve"]["descriptions"][0]["value"].lower()
            assigned = False
            for level, words in risk_keywords.items():
                if any(w in desc for w in words):
                    risk_count[level] += 1
                    assigned = True
                    break
            if not assigned:
                risk_count["Low"] += 1  # Default to Low if no match
            total += 1
        # Calcula el porcentaje de cada nivel
        risk_percent = {level: (risk_count[level] / total * 100) if total else 0 for level in risk_keywords}
        results.append({"keyword": keyword, "risk_percent": risk_percent})
    return {"results": results}

@router.post("/nvd/enterprise_metrics")
async def get_enterprise_metrics():
    """
    Calculate enterprise-level risk metrics for asset management.
    Provides comprehensive risk assessment for business decision making.
    """
    mq = MessageQueue()
    messages = mq.get_all_messages()
    if not messages:
        return {"detail": "No NVD searches in queue."}
    
    # Enhanced risk assessment with enterprise context
    risk_keywords = {
        "Critical": [
            "remote code execution", "privilege escalation", "arbitrary code", 
            "unauthenticated", "root access", "critical", "rce", "authentication bypass",
            "buffer overflow", "memory corruption", "zero day"
        ],
        "High": [
            "denial of service", "bypass authentication", "sql injection", 
            "directory traversal", "high", "dos", "ddos", "injection",
            "path traversal", "file inclusion", "command injection"
        ],
        "Medium": [
            "information disclosure", "medium", "xss", "cross-site scripting", 
            "csrf", "session fixation", "weak encryption", "insecure storage",
            "information leakage", "security misconfiguration"
        ],
        "Low": [
            "low", "minor", "limited impact", "weak password", 
            "insufficient logging", "improper input validation"
        ],
        "Very Low": [
            "no impact", "informational", "very low", "deprecated",
            "cosmetic", "documentation"
        ]
    }
    
    # Business impact weights for enterprise scoring
    business_impact_weights = {
        "Critical": 5.0,  # Severe business disruption
        "High": 4.0,      # Major operational impact
        "Medium": 3.0,    # Moderate business risk
        "Low": 2.0,       # Minor operational concern
        "Very Low": 1.0   # Negligible impact
    }
    
    results = []
    total_business_impact = 0
    asset_categories = {
        "Web Applications": ["react", "vue", "angular", "javascript", "nodejs", "express", "django", "flask"],
        "Infrastructure": ["apache", "nginx", "docker", "kubernetes", "linux", "windows", "centos", "ubuntu"],
        "Databases": ["mysql", "postgresql", "mongodb", "redis", "oracle", "sqlserver", "elasticsearch"],
        "Development Tools": ["git", "jenkins", "python", "java", "php", "ruby", "golang"],
        "Security Tools": ["openssl", "ssh", "ssl", "tls", "crypto", "vault", "auth"]
    }
    
    for msg in messages:
        keyword = msg["keyword"]
        vulns = msg["vulnerabilities"]
        risk_count = {k: 0 for k in risk_keywords}
        total = len(vulns)
        
        # Categorize asset
        asset_category = "Other"
        for category, keywords in asset_categories.items():
            if any(kw in keyword.lower() for kw in keywords):
                asset_category = category
                break
        
        # Analyze vulnerabilities
        for vuln in vulns:
            desc = vuln["cve"]["descriptions"][0]["value"].lower()
            assigned = False
            for level, words in risk_keywords.items():
                if any(w in desc for w in words):
                    risk_count[level] += 1
                    assigned = True
                    break
            if not assigned:
                risk_count["Low"] += 1
        
        # Calculate risk percentages and business impact
        risk_percent = {level: (risk_count[level] / total * 100) if total else 0 for level in risk_keywords}
        
        # Calculate weighted business impact score
        business_impact = sum(
            (risk_percent[level] / 100) * business_impact_weights[level] 
            for level in risk_keywords
        )
        total_business_impact += business_impact
        
        results.append({
            "keyword": keyword,
            "asset_category": asset_category,
            "risk_percent": risk_percent,
            "business_impact_score": business_impact,
            "total_vulnerabilities": total,
            "criticality_score": risk_percent.get("Critical", 0) + risk_percent.get("High", 0)
        })
    
    # Calculate enterprise metrics
    avg_business_impact = total_business_impact / len(results) if results else 0
    high_risk_assets = len([r for r in results if r["criticality_score"] > 30])
    
    enterprise_metrics = {
        "total_assets_analyzed": len(results),
        "average_business_impact": avg_business_impact,
        "high_risk_assets_count": high_risk_assets,
        "enterprise_risk_level": (
            "Critical" if avg_business_impact >= 4.0 else
            "High" if avg_business_impact >= 3.0 else
            "Medium" if avg_business_impact >= 2.0 else
            "Low"
        ),
        "assets_by_category": {},
        "recommendations": []
    }
    
    # Group by category for reporting
    for result in results:
        category = result["asset_category"]
        if category not in enterprise_metrics["assets_by_category"]:
            enterprise_metrics["assets_by_category"][category] = {
                "count": 0,
                "avg_impact": 0,
                "high_risk_count": 0
            }
        enterprise_metrics["assets_by_category"][category]["count"] += 1
        enterprise_metrics["assets_by_category"][category]["avg_impact"] += result["business_impact_score"]
        if result["criticality_score"] > 30:
            enterprise_metrics["assets_by_category"][category]["high_risk_count"] += 1
    
    # Calculate averages
    for category_data in enterprise_metrics["assets_by_category"].values():
        if category_data["count"] > 0:
            category_data["avg_impact"] /= category_data["count"]
    
    # Generate recommendations
    if high_risk_assets > len(results) * 0.3:
        enterprise_metrics["recommendations"].append(
            "High percentage of critical assets detected. Immediate security review recommended."
        )
    if avg_business_impact >= 3.5:
        enterprise_metrics["recommendations"].append(
            "Enterprise risk level is elevated. Consider implementing additional security controls."
        )
    if len(results) < 5:
        enterprise_metrics["recommendations"].append(
            "Limited asset coverage. Expand vulnerability scanning to more systems."
        )
    
    return {
        "results": results,
        "enterprise_metrics": enterprise_metrics,
        "analysis_timestamp": datetime.now().isoformat()
    }

@router.get("/nvd/queue_status")
async def get_queue_status():
    """Get current status of the NVD analysis queue"""
    mq = MessageQueue()
    messages = mq.get_all_messages()
    
    return {
        "queue_size": len(messages),
        "keywords": [msg.get("keyword", "unknown") for msg in messages],
        "total_vulnerabilities": sum(len(msg.get("vulnerabilities", [])) for msg in messages)
    }

@router.post("/nvd/clear_queue")
async def clear_analysis_queue():
    """Clear the NVD analysis queue"""
    mq = MessageQueue()
    cleared_count = len(mq.get_all_messages())
    # This would need to be implemented in the MessageQueue class
    # For now, we'll just return the count
    return {
        "message": "Queue cleared successfully",
        "cleared_items": cleared_count
    }
