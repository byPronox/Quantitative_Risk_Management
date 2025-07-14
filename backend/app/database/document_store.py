"""
DocumentStore for consuming NVD service data and storing in MongoDB.
Handles data retrieval, processing, and storage with proper error handling.
"""
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from database.mongodb import MongoDBConnection
from config.config import Settings

# Create settings instance
settings = Settings()

logger = logging.getLogger(__name__)

class DocumentStore:
    """
    Service for consuming NVD vulnerability data and storing in MongoDB.
    Manages data retrieval from nvd_service and document storage.
    """
    
    def __init__(self):
        self.nvd_endpoint = f"{settings.NVD_SERVICE_URL}/nvd/results/all"
        self.collection_name = "nvd_vulnerabilities"
    
    async def fetch_nvd_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch vulnerability data from NVD service.
        
        Returns:
            Dictionary containing vulnerability data or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.nvd_endpoint)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched NVD data: {len(data.get('vulnerabilities', []))} vulnerabilities")
                return data
                
        except httpx.RequestError as e:
            logger.error(f"Request failed when fetching NVD data: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when fetching NVD data: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching NVD data: {e}")
            return None
    
    async def process_and_store_vulnerabilities(self, nvd_data: Dict[str, Any]) -> bool:
        """
        Process NVD data and store vulnerabilities in MongoDB.
        
        Args:
            nvd_data: Raw data from NVD service
            
        Returns:
            True if successfully stored, False otherwise
        """
        try:
            db = MongoDBConnection.get_database()
            collection = db[self.collection_name]
            
            # Extract vulnerabilities from the response
            vulnerabilities = nvd_data.get('vulnerabilities', [])
            search_metadata = nvd_data.get('metadata', {})
            
            if not vulnerabilities:
                logger.warning("No vulnerabilities found in NVD data")
                return True
            
            # Process each vulnerability and prepare for storage
            documents_to_insert = []
            current_time = datetime.now(timezone.utc)
            
            for vuln in vulnerabilities:
                document = {
                    "cve_id": vuln.get('cve', {}).get('id', 'Unknown'),
                    "software": self._extract_software_info(vuln),
                    "task_id": search_metadata.get('task_id', f"task_{current_time.strftime('%Y%m%d_%H%M%S')}"),
                    "vulnerability_data": vuln,
                    "severity": self._extract_severity(vuln),
                    "published_date": vuln.get('cve', {}).get('published', None),
                    "last_modified": vuln.get('cve', {}).get('lastModified', None),
                    "search_keywords": search_metadata.get('keywords', []),
                    "analysis_timestamp": current_time,
                    "source": "nvd_service",
                    "business_impact": self._calculate_business_impact(vuln),
                    "asset_categories": self._categorize_assets(vuln)
                }
                documents_to_insert.append(document)
            
            # Insert documents into MongoDB
            if documents_to_insert:
                result = await collection.insert_many(documents_to_insert)
                logger.info(f"Successfully inserted {len(result.inserted_ids)} vulnerability documents")
                
                # Also store search session for reporting
                await self._store_search_session(db, search_metadata, vulnerabilities, current_time)
                
                return True
            else:
                logger.warning("No documents prepared for insertion")
                return False
                
        except Exception as e:
            logger.error(f"Error processing and storing vulnerabilities: {e}")
            return False
    
    async def _store_search_session(self, db, metadata: Dict, vulnerabilities: List, timestamp: datetime):
        """Store search session information for report generation."""
        try:
            search_collection = db["search_sessions"]
            
            session_doc = {
                "session_id": metadata.get('task_id', f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}"),
                "search_keywords": metadata.get('keywords', []),
                "total_vulnerabilities": len(vulnerabilities),
                "search_timestamp": timestamp,
                "vulnerability_summary": {
                    "critical": len([v for v in vulnerabilities if self._extract_severity(v) == "Critical"]),
                    "high": len([v for v in vulnerabilities if self._extract_severity(v) == "High"]),
                    "medium": len([v for v in vulnerabilities if self._extract_severity(v) == "Medium"]),
                    "low": len([v for v in vulnerabilities if self._extract_severity(v) == "Low"])
                },
                "metadata": metadata
            }
            
            await search_collection.insert_one(session_doc)
            logger.info(f"Search session stored: {session_doc['session_id']}")
            
        except Exception as e:
            logger.error(f"Error storing search session: {e}")
    
    def _extract_software_info(self, vulnerability: Dict) -> List[str]:
        """Extract software information from vulnerability data."""
        software_list = []
        
        try:
            configurations = vulnerability.get('cve', {}).get('configurations', [])
            for config in configurations:
                nodes = config.get('nodes', [])
                for node in nodes:
                    cpe_matches = node.get('cpeMatch', [])
                    for cpe in cpe_matches:
                        criteria = cpe.get('criteria', '')
                        if criteria and ':' in criteria:
                            parts = criteria.split(':')
                            if len(parts) >= 4:
                                vendor = parts[3]
                                product = parts[4]
                                software_list.append(f"{vendor}:{product}")
        except Exception as e:
            logger.warning(f"Error extracting software info: {e}")
        
        return list(set(software_list)) if software_list else ["Unknown"]
    
    def _extract_severity(self, vulnerability: Dict) -> str:
        """Extract severity level from vulnerability data."""
        try:
            metrics = vulnerability.get('cve', {}).get('metrics', {})
            
            # Try CVSS v3 first
            cvss_v3 = metrics.get('cvssMetricV3', [])
            if cvss_v3:
                base_score = cvss_v3[0].get('cvssData', {}).get('baseScore', 0)
                return self._score_to_severity(base_score)
            
            # Fallback to CVSS v2
            cvss_v2 = metrics.get('cvssMetricV2', [])
            if cvss_v2:
                base_score = cvss_v2[0].get('cvssData', {}).get('baseScore', 0)
                return self._score_to_severity(base_score)
                
        except Exception as e:
            logger.warning(f"Error extracting severity: {e}")
        
        return "Unknown"
    
    def _score_to_severity(self, score: float) -> str:
        """Convert CVSS score to severity level."""
        if score >= 9.0:
            return "Critical"
        elif score >= 7.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        elif score > 0.0:
            return "Low"
        else:
            return "None"
    
    def _calculate_business_impact(self, vulnerability: Dict) -> Dict[str, Any]:
        """Calculate business impact based on vulnerability characteristics."""
        severity = self._extract_severity(vulnerability)
        software = self._extract_software_info(vulnerability)
        
        # Business impact calculation logic
        impact_score = 0
        if severity == "Critical":
            impact_score = 100
        elif severity == "High":
            impact_score = 75
        elif severity == "Medium":
            impact_score = 50
        elif severity == "Low":
            impact_score = 25
        
        return {
            "impact_score": impact_score,
            "severity_level": severity,
            "affected_software": software,
            "recommendation": self._get_recommendation(severity)
        }
    
    def _categorize_assets(self, vulnerability: Dict) -> List[str]:
        """Categorize assets based on software affected."""
        software = self._extract_software_info(vulnerability)
        categories = set()
        
        for sw in software:
            sw_lower = sw.lower()
            if any(tech in sw_lower for tech in ['apache', 'nginx', 'iis', 'tomcat']):
                categories.add('Infrastructure')
            elif any(tech in sw_lower for tech in ['mysql', 'postgresql', 'mongodb', 'oracle']):
                categories.add('Database')
            elif any(tech in sw_lower for tech in ['node', 'react', 'angular', 'vue']):
                categories.add('Web Applications')
            elif any(tech in sw_lower for tech in ['git', 'jenkins', 'docker']):
                categories.add('Development Tools')
            elif any(tech in sw_lower for tech in ['openssl', 'ssh', 'ssl']):
                categories.add('Security Tools')
            else:
                categories.add('Other')
        
        return list(categories) if categories else ['Other']
    
    def _get_recommendation(self, severity: str) -> str:
        """Get recommendation based on severity level."""
        recommendations = {
            "Critical": "Immediate action required. Patch or mitigate within 24 hours.",
            "High": "High priority. Patch or mitigate within 72 hours.",
            "Medium": "Medium priority. Plan patching within 1-2 weeks.",
            "Low": "Low priority. Include in next maintenance cycle.",
            "Unknown": "Review manually and assess risk level."
        }
        return recommendations.get(severity, "Review and assess manually.")
    
    async def consume_and_store(self) -> bool:
        """
        Main method to consume NVD service data and store in MongoDB.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting NVD data consumption and storage process")
        
        # Fetch data from NVD service
        nvd_data = await self.fetch_nvd_data()
        if not nvd_data:
            logger.error("Failed to fetch NVD data")
            return False
        
        # Process and store the data
        success = await self.process_and_store_vulnerabilities(nvd_data)
        if success:
            logger.info("NVD data consumption and storage completed successfully")
        else:
            logger.error("Failed to process and store NVD data")
        
        return success
    
    async def get_search_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search sessions for report generation."""
        try:
            db = MongoDBConnection.get_database()
            collection = db["search_sessions"]
            
            cursor = collection.find({}).sort("search_timestamp", -1).limit(limit)
            sessions = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for session in sessions:
                session['_id'] = str(session['_id'])
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error fetching search sessions: {e}")
            return []
    
    async def get_vulnerabilities_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get vulnerabilities for a specific search session."""
        try:
            db = MongoDBConnection.get_database()
            collection = db[self.collection_name]
            
            cursor = collection.find({"task_id": session_id})
            vulnerabilities = await cursor.to_list(length=None)
            
            # Convert ObjectId to string for JSON serialization
            for vuln in vulnerabilities:
                vuln['_id'] = str(vuln['_id'])
            
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Error fetching vulnerabilities for session {session_id}: {e}")
            return []
