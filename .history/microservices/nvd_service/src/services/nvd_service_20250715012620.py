"""
NVD API Service for vulnerability data retrieval and processing.
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class NVDAPIService:
    """Service for interacting with the National Vulnerability Database API."""
    
    def __init__(self):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = os.getenv("NVD_API_KEY", "")
        self.kong_proxy_url = os.getenv("KONG_PROXY_URL", "")
        self.use_kong = os.getenv("USE_KONG_NVD", "false").lower() == "true"
        
    def _get_api_config(self) -> Dict[str, Any]:
        """Get API configuration based on environment settings."""
        if self.kong_proxy_url and self.use_kong:
            # Use Kong Gateway as proxy
            return {
                "url": f"{self.kong_proxy_url}/nvd-api/cves/2.0",
                "headers": {"X-Kong-Client": "nvd-service"}
            }
        else:
            # Direct NVD API connection
            return {
                "url": self.base_url,
                "headers": {"apiKey": self.api_key} if self.api_key else {}
            }
    
    async def search_vulnerabilities(
        self, 
        keyword: str, 
        start_index: int = 0, 
        results_per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Search for vulnerabilities using a keyword.
        
        Args:
            keyword: Search keyword
            start_index: Starting index for pagination
            results_per_page: Number of results per page
            
        Returns:
            Dict containing vulnerability data
        """
        config = self._get_api_config()
        params = {
            "keywordSearch": keyword,
            "startIndex": start_index,
            "resultsPerPage": results_per_page
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    config["url"],
                    headers=config["headers"],
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(
                    "NVD search successful for keyword '%s' via %s",
                    keyword,
                    "Kong Gateway" if self.use_kong else "Direct API"
                )
                
                return {
                    "vulnerabilities": data.get("vulnerabilities", []),
                    "total_results": data.get("totalResults", 0),
                    "results_per_page": data.get("resultsPerPage", 0),
                    "start_index": data.get("startIndex", 0)
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"NVD API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"NVD API request failed: {e}")
            raise

    async def get_vulnerability(self, cve_id: str) -> Dict[str, Any]:
        """
        Get a specific vulnerability by CVE ID.
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2023-1234)
            
        Returns:
            Dict containing vulnerability data
        """
        config = self._get_api_config()
        params = {"cveId": cve_id}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    config["url"],
                    headers=config["headers"],
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])
                
                if not vulnerabilities:
                    logger.warning(f"CVE {cve_id} not found")
                    return None
                
                logger.info(
                    "Retrieved CVE %s via %s",
                    cve_id,
                    "Kong Gateway" if self.use_kong else "Direct API"
                )
                
                return vulnerabilities[0]
                
        except httpx.HTTPStatusError as e:
            logger.error(f"NVD API HTTP error for CVE {cve_id}: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Failed to get CVE {cve_id}: {e}")
            raise

    async def search_by_cpe(self, cpe_name: str, start_index: int = 0, results_per_page: int = 10) -> Dict[str, Any]:
        """
        Search for vulnerabilities by CPE name.
        
        Args:
            cpe_name: CPE name to search for
            start_index: Starting index for pagination
            results_per_page: Number of results per page
            
        Returns:
            Dict containing vulnerability data
        """
        config = self._get_api_config()
        params = {
            "cpeName": cpe_name,
            "startIndex": start_index,
            "resultsPerPage": results_per_page
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    config["url"],
                    headers=config["headers"],
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(
                    "NVD CPE search successful for '%s' via %s",
                    cpe_name,
                    "Kong Gateway" if self.use_kong else "Direct API"
                )
                
                return {
                    "vulnerabilities": data.get("vulnerabilities", []),
                    "total_results": data.get("totalResults", 0),
                    "results_per_page": data.get("resultsPerPage", 0),
                    "start_index": data.get("startIndex", 0)
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"NVD API HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"NVD CPE search failed: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if the NVD API is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            config = self._get_api_config()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Simple request with minimal parameters
                response = await client.get(
                    config["url"],
                    headers=config["headers"],
                    params={"resultsPerPage": 1}
                )
                response.raise_for_status()
                
                logger.debug("NVD API health check passed")
                return True
                
        except Exception as e:
            logger.warning(f"NVD API health check failed: {e}")
            return False


class NVDService:
    """
    High-level NVD service that orchestrates API calls and data processing.
    """
    
    def __init__(self):
        self.api_service = NVDAPIService()
    
    async def search_vulnerabilities(
        self,
        keywords: Optional[str] = None,
        cve_id: Optional[str] = None,
        cpe_name: Optional[str] = None,
        results_per_page: int = 20,
        start_index: int = 0,
        pub_start_date: Optional[str] = None,
        pub_end_date: Optional[str] = None,
        last_mod_start_date: Optional[str] = None,
        last_mod_end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for vulnerabilities with flexible parameters.
        """
        if cve_id:
            # Single CVE lookup
            result = await self.api_service.get_vulnerability(cve_id)
            return {
                "vulnerabilities": [result] if result else [],
                "total_results": 1 if result else 0,
                "results_per_page": 1,
                "start_index": 0,
                "format": "NVD_CVE",
                "version": "2.0",
                "timestamp": datetime.utcnow().isoformat()
            }
        elif cpe_name:
            # CPE-based search
            return await self.api_service.search_by_cpe(cpe_name, start_index, results_per_page)
        elif keywords and keywords.strip():
            # Keyword search (only if keywords is not empty)
            return await self.api_service.search_vulnerabilities(keywords, start_index, results_per_page)
        else:
            # Default search with a general term if no parameters provided
            default_keyword = "vulnerability"
            return await self.api_service.search_vulnerabilities(default_keyword, start_index, results_per_page)
    
    async def get_vulnerability(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific vulnerability by CVE ID.
        """
        return await self.api_service.get_vulnerability(cve_id)
    
    async def health_check(self) -> bool:
        """
        Check service health.
        """
        return await self.api_service.health_check()
