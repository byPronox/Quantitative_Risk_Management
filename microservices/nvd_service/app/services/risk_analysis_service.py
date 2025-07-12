"""
Risk Analysis Service for vulnerability assessment and enterprise metrics.
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskAnalysisService:
    """Service for analyzing vulnerability risks and calculating enterprise metrics."""
    
    def __init__(self):
        # Risk classification keywords
        self.risk_keywords = {
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
        self.business_impact_weights = {
            "Critical": 5.0,  # Severe business disruption
            "High": 4.0,      # Major operational impact
            "Medium": 3.0,    # Moderate business risk
            "Low": 2.0,       # Minor operational concern
            "Very Low": 1.0   # Negligible impact
        }
        
        # Asset categorization keywords
        self.asset_categories = {
            "Web Applications": ["react", "vue", "angular", "javascript", "nodejs", "express", "django", "flask"],
            "Infrastructure": ["apache", "nginx", "docker", "kubernetes", "linux", "windows", "centos", "ubuntu"],
            "Databases": ["mysql", "postgresql", "mongodb", "redis", "oracle", "sqlserver", "elasticsearch"],
            "Development Tools": ["git", "jenkins", "python", "java", "php", "ruby", "golang"],
            "Security Tools": ["openssl", "ssh", "ssl", "tls", "crypto", "vault", "auth"]
        }
    
    def analyze_vulnerability_risks(self, vulnerabilities_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze risks from vulnerability data.
        
        Args:
            vulnerabilities_data: List of vulnerability data from queue
            
        Returns:
            List of risk analysis results
        """
        results = []
        
        for vuln_data in vulnerabilities_data:
            keyword = vuln_data.get("keyword", "unknown")
            vulnerabilities = vuln_data.get("vulnerabilities", [])
            
            risk_analysis = self._analyze_single_keyword(keyword, vulnerabilities)
            results.append(risk_analysis)
        
        return results
    
    def _analyze_single_keyword(self, keyword: str, vulnerabilities: List[Dict]) -> Dict[str, Any]:
        """Analyze risks for a single keyword's vulnerabilities."""
        risk_count = {level: 0 for level in self.risk_keywords}
        total = len(vulnerabilities)
        
        for vuln in vulnerabilities:
            try:
                description = vuln["cve"]["descriptions"][0]["value"].lower()
                assigned = False
                
                for level, keywords in self.risk_keywords.items():
                    if any(kw in description for kw in keywords):
                        risk_count[level] += 1
                        assigned = True
                        break
                
                if not assigned:
                    risk_count["Low"] += 1  # Default to Low if no match
                    
            except (KeyError, IndexError) as e:
                logger.warning(f"Error processing vulnerability: {e}")
                risk_count["Low"] += 1
        
        # Calculate risk percentages
        risk_percent = {
            level: (risk_count[level] / total * 100) if total > 0 else 0 
            for level in self.risk_keywords
        }
        
        return {
            "keyword": keyword,
            "risk_percent": risk_percent,
            "total_vulnerabilities": total,
            "risk_count": risk_count
        }
    
    def calculate_enterprise_metrics(self, vulnerabilities_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive enterprise risk metrics.
        
        Args:
            vulnerabilities_data: List of vulnerability data from queue
            
        Returns:
            Enterprise metrics and recommendations
        """
        if not vulnerabilities_data:
            return {"error": "No vulnerability data available for analysis"}
        
        results = []
        total_business_impact = 0
        
        for vuln_data in vulnerabilities_data:
            keyword = vuln_data.get("keyword", "unknown")
            vulnerabilities = vuln_data.get("vulnerabilities", [])
            
            # Analyze risks
            risk_analysis = self._analyze_single_keyword(keyword, vulnerabilities)
            
            # Categorize asset
            asset_category = self._categorize_asset(keyword)
            
            # Calculate business impact
            business_impact = self._calculate_business_impact(risk_analysis["risk_percent"])
            total_business_impact += business_impact
            
            # Calculate criticality score
            criticality_score = (
                risk_analysis["risk_percent"].get("Critical", 0) + 
                risk_analysis["risk_percent"].get("High", 0)
            )
            
            results.append({
                "keyword": keyword,
                "asset_category": asset_category,
                "risk_percent": risk_analysis["risk_percent"],
                "business_impact_score": business_impact,
                "total_vulnerabilities": risk_analysis["total_vulnerabilities"],
                "criticality_score": criticality_score
            })
        
        # Calculate enterprise-wide metrics
        enterprise_metrics = self._calculate_enterprise_summary(results, total_business_impact)
        
        return {
            "results": results,
            "enterprise_metrics": enterprise_metrics,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _categorize_asset(self, keyword: str) -> str:
        """Categorize asset based on keyword."""
        keyword_lower = keyword.lower()
        
        for category, keywords in self.asset_categories.items():
            if any(kw in keyword_lower for kw in keywords):
                return category
        
        return "Other"
    
    def _calculate_business_impact(self, risk_percent: Dict[str, float]) -> float:
        """Calculate weighted business impact score."""
        return sum(
            (risk_percent[level] / 100) * self.business_impact_weights[level]
            for level in self.risk_keywords
        )
    
    def _calculate_enterprise_summary(self, results: List[Dict], total_business_impact: float) -> Dict[str, Any]:
        """Calculate enterprise-wide summary metrics."""
        if not results:
            return {}
        
        avg_business_impact = total_business_impact / len(results)
        high_risk_assets = len([r for r in results if r["criticality_score"] > 30])
        
        # Determine enterprise risk level
        if avg_business_impact >= 4.0:
            enterprise_risk_level = "Critical"
        elif avg_business_impact >= 3.0:
            enterprise_risk_level = "High"
        elif avg_business_impact >= 2.0:
            enterprise_risk_level = "Medium"
        else:
            enterprise_risk_level = "Low"
        
        # Group by category
        assets_by_category = {}
        for result in results:
            category = result["asset_category"]
            if category not in assets_by_category:
                assets_by_category[category] = {
                    "count": 0,
                    "avg_impact": 0,
                    "high_risk_count": 0
                }
            
            assets_by_category[category]["count"] += 1
            assets_by_category[category]["avg_impact"] += result["business_impact_score"]
            if result["criticality_score"] > 30:
                assets_by_category[category]["high_risk_count"] += 1
        
        # Calculate averages
        for category_data in assets_by_category.values():
            if category_data["count"] > 0:
                category_data["avg_impact"] /= category_data["count"]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results, high_risk_assets, avg_business_impact)
        
        return {
            "total_assets_analyzed": len(results),
            "average_business_impact": avg_business_impact,
            "high_risk_assets_count": high_risk_assets,
            "enterprise_risk_level": enterprise_risk_level,
            "assets_by_category": assets_by_category,
            "recommendations": recommendations
        }
    
    def _generate_recommendations(self, results: List[Dict], high_risk_assets: int, avg_impact: float) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if high_risk_assets > len(results) * 0.3:
            recommendations.append(
                "High percentage of critical assets detected. Immediate security review recommended."
            )
        
        if avg_impact >= 3.5:
            recommendations.append(
                "Enterprise risk level is elevated. Consider implementing additional security controls."
            )
        
        if len(results) < 5:
            recommendations.append(
                "Limited asset coverage. Expand vulnerability scanning to more systems."
            )
        
        # Category-specific recommendations
        categories = set(r["asset_category"] for r in results)
        if "Web Applications" in categories:
            recommendations.append(
                "Web application assets detected. Ensure WAF and secure coding practices are in place."
            )
        
        if "Infrastructure" in categories:
            recommendations.append(
                "Infrastructure assets require regular patching and configuration management."
            )
        
        return recommendations
