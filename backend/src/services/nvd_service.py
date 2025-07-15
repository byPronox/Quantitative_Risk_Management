"""
NVD (National Vulnerability Database) service
"""
import logging
from typing import Dict, Any, List, Optional
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class NVDService:
    """Service for NVD API interactions"""
    
    def __init__(self):
        self.api_key = settings.NVD_API_KEY
        self.base_url = "https://services.nvd.nist.gov/rest/json"
        self.headers = {
            "apiKey": self.api_key
        } if self.api_key else {}
    
    async def get_vulnerabilities(
        self,
        cpe_name: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get vulnerabilities from NVD API
        """
        try:
            params = {
                "resultsPerPage": min(limit, 2000),  # NVD API limit
                "startIndex": 0
            }
            
            if cpe_name:
                params["cpeName"] = cpe_name
            if keyword:
                params["keywordSearch"] = keyword
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/cves/2.0",
                    params=params,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = self._parse_nvd_response(data)
                    return {
                        "vulnerabilities": vulnerabilities,
                        "total_results": data.get("totalResults", 0),
                        "risk_score": self._calculate_nvd_risk_score(vulnerabilities)
                    }
                else:
                    logger.error(f"NVD API error: {response.status_code}")
                    return {"vulnerabilities": [], "total_results": 0, "risk_score": 0.0}
                    
        except Exception as e:
            logger.error(f"NVD API request failed: {e}")
            return {"vulnerabilities": [], "total_results": 0, "risk_score": 0.0}
    
    async def search_cpe(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for CPE entries
        """
        try:
            params = {
                "keywordSearch": keyword,
                "resultsPerPage": min(limit, 10000)  # CPE API limit
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/cpes/2.0",
                    params=params,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_cpe_response(data)
                else:
                    logger.error(f"NVD CPE API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"NVD CPE API request failed: {e}")
            return []
    
    async def analyze_software_list(self, software_list: List[str]) -> Dict[str, Any]:
        """
        Analyze a list of software for vulnerabilities
        """
        results = {
            "software_analyzed": len(software_list),
            "total_vulnerabilities": 0,
            "high_risk_software": [],
            "analysis_results": []
        }
        
        for software in software_list:
            try:
                # Search for vulnerabilities by keyword
                vuln_data = await self.get_vulnerabilities(keyword=software, limit=50)
                
                software_result = {
                    "software": software,
                    "vulnerabilities_found": len(vuln_data["vulnerabilities"]),
                    "risk_score": vuln_data["risk_score"],
                    "critical_vulns": len([
                        v for v in vuln_data["vulnerabilities"] 
                        if v.get("cvss_score", 0) >= 9.0
                    ])
                }
                
                results["analysis_results"].append(software_result)
                results["total_vulnerabilities"] += software_result["vulnerabilities_found"]
                
                if software_result["risk_score"] >= 7.0:
                    results["high_risk_software"].append(software)
                    
            except Exception as e:
                logger.error(f"Failed to analyze software {software}: {e}")
        
        return results
    
    def _parse_nvd_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse NVD vulnerability response"""
        vulnerabilities = []
        
        for vuln in data.get("vulnerabilities", []):
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")
            
            # Extract CVSS score
            cvss_score = None
            metrics = cve.get("metrics", {})
            if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                cvss_score = metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseScore")
            elif "cvssMetricV3" in metrics and metrics["cvssMetricV3"]:
                cvss_score = metrics["cvssMetricV3"][0].get("cvssData", {}).get("baseScore")
            elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                cvss_score = metrics["cvssMetricV2"][0].get("cvssData", {}).get("baseScore")
            
            # Extract description
            descriptions = cve.get("descriptions", [])
            description = ""
            if descriptions:
                description = descriptions[0].get("value", "")
            
            vulnerabilities.append({
                "cve_id": cve_id,
                "description": description,
                "cvss_score": cvss_score,
                "severity": self._get_severity_from_score(cvss_score),
                "published_date": cve.get("published"),
                "last_modified": cve.get("lastModified")
            })
        
        return vulnerabilities
    
    def _parse_cpe_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse NVD CPE response"""
        cpe_list = []
        
        for product in data.get("products", []):
            cpe = product.get("cpe", {})
            cpe_list.append({
                "cpe_name": cpe.get("cpeName", ""),
                "title": cpe.get("titles", [{}])[0].get("title", "") if cpe.get("titles") else "",
                "deprecated": cpe.get("deprecated", False),
                "last_modified": cpe.get("lastModified")
            })
        
        return cpe_list
    
    def _calculate_nvd_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate risk score based on NVD vulnerabilities"""
        if not vulnerabilities:
            return 0.0
        
        total_score = 0.0
        scored_vulns = 0
        
        for vuln in vulnerabilities:
            cvss_score = vuln.get("cvss_score")
            if cvss_score is not None:
                total_score += cvss_score
                scored_vulns += 1
        
        if scored_vulns == 0:
            return 0.0
        
        avg_score = total_score / scored_vulns
        # Adjust for vulnerability count (more vulns = higher risk)
        count_factor = min(len(vulnerabilities) * 0.1, 2.0)
        
        return min(avg_score + count_factor, 10.0)
    
    def _get_severity_from_score(self, cvss_score: Optional[float]) -> str:
        """Convert CVSS score to severity level"""
        if cvss_score is None:
            return "unknown"
        elif cvss_score >= 9.0:
            return "critical"
        elif cvss_score >= 7.0:
            return "high"
        elif cvss_score >= 4.0:
            return "medium"
        else:
            return "low"
