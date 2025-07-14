import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database import MongoDBConnection
from app.api.schemas import VulnerabilityData, ReportMetrics, ReportType
import httpx
import logging

logger = logging.getLogger(__name__)

class DataService:
    """Service to fetch and process vulnerability data for reports"""
    
    @staticmethod
    async def get_vulnerability_data(session_id: Optional[str] = None, 
                                   date_range: Optional[Dict[str, str]] = None,
                                   filters: Optional[Dict[str, Any]] = None) -> List[VulnerabilityData]:
        """
        Fetch vulnerability data from MongoDB based on filters
        """
        try:
            db = MongoDBConnection.get_database()
            collection = db.vulnerability_sessions
            
            # Build query
            query = {}
            
            if session_id:
                query["session_id"] = session_id
            
            if date_range:
                date_query = {}
                if date_range.get("start_date"):
                    date_query["$gte"] = datetime.fromisoformat(date_range["start_date"])
                if date_range.get("end_date"):
                    date_query["$lte"] = datetime.fromisoformat(date_range["end_date"])
                if date_query:
                    query["created_at"] = date_query
            
            if filters:
                if filters.get("severity"):
                    query["vulnerabilities.baseMetricV3.cvssV3.baseSeverity"] = filters["severity"]
                if filters.get("min_score"):
                    query["vulnerabilities.baseMetricV3.cvssV3.baseScore"] = {"$gte": filters["min_score"]}
            
            # Fetch documents
            cursor = collection.find(query).sort("created_at", -1).limit(100)
            documents = await cursor.to_list(length=100)
            
            # Process vulnerabilities from all sessions
            vulnerabilities = []
            for doc in documents:
                for vuln in doc.get("vulnerabilities", []):
                    try:
                        # Extract CVSS data
                        impact = vuln.get("impact", {})
                        base_metric = impact.get("baseMetricV3", {})
                        cvss_v3 = base_metric.get("cvssV3", {})
                        
                        # Get basic vulnerability info
                        cve_data = vuln.get("cve", {})
                        cve_id = cve_data.get("CVE_data_meta", {}).get("ID", "Unknown")
                        
                        # Get descriptions
                        descriptions = cve_data.get("description", {}).get("description_data", [])
                        description = descriptions[0].get("value", "No description available") if descriptions else "No description available"
                        
                        # Get affected products
                        affects = cve_data.get("affects", {}).get("vendor", {}).get("vendor_data", [])
                        affected_products = []
                        for vendor in affects:
                            for product in vendor.get("product", {}).get("product_data", []):
                                affected_products.append(f"{vendor.get('vendor_name', 'Unknown')}: {product.get('product_name', 'Unknown')}")
                        
                        vulnerability = VulnerabilityData(
                            cve_id=cve_id,
                            severity=cvss_v3.get("baseSeverity", "UNKNOWN"),
                            score=float(cvss_v3.get("baseScore", 0.0)),
                            description=description[:500] + "..." if len(description) > 500 else description,
                            affected_products=affected_products[:5],  # Limit to 5 products
                            published_date=datetime.fromisoformat(vuln.get("publishedDate", "2024-01-01T00:00:00.000").replace("Z", "+00:00")),
                            business_impact=doc.get("business_impact", "Medium")
                        )
                        vulnerabilities.append(vulnerability)
                        
                    except Exception as e:
                        logger.warning(f"Error processing vulnerability {vuln.get('cve', {}).get('CVE_data_meta', {}).get('ID', 'Unknown')}: {e}")
                        continue
            
            return vulnerabilities[:1000]  # Limit to 1000 vulnerabilities
            
        except Exception as e:
            logger.error(f"Error fetching vulnerability data: {e}")
            return []
    
    @staticmethod
    def calculate_metrics(vulnerabilities: List[VulnerabilityData]) -> ReportMetrics:
        """Calculate metrics from vulnerability data"""
        if not vulnerabilities:
            return ReportMetrics(
                total_vulnerabilities=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                average_score=0.0,
                risk_distribution={}
            )
        
        # Count by severity
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        total_score = 0.0
        
        for vuln in vulnerabilities:
            severity = vuln.severity.upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts["UNKNOWN"] += 1
            total_score += vuln.score
        
        # Calculate risk distribution by score ranges
        risk_distribution = {
            "Critical (9.0-10.0)": len([v for v in vulnerabilities if v.score >= 9.0]),
            "High (7.0-8.9)": len([v for v in vulnerabilities if 7.0 <= v.score < 9.0]),
            "Medium (4.0-6.9)": len([v for v in vulnerabilities if 4.0 <= v.score < 7.0]),
            "Low (0.1-3.9)": len([v for v in vulnerabilities if 0.1 <= v.score < 4.0]),
            "None (0.0)": len([v for v in vulnerabilities if v.score == 0.0])
        }
        
        return ReportMetrics(
            total_vulnerabilities=len(vulnerabilities),
            critical_count=severity_counts["CRITICAL"],
            high_count=severity_counts["HIGH"],
            medium_count=severity_counts["MEDIUM"],
            low_count=severity_counts["LOW"],
            average_score=total_score / len(vulnerabilities) if vulnerabilities else 0.0,
            risk_distribution=risk_distribution
        )
    
    @staticmethod
    async def get_session_info(session_id: str) -> Dict[str, Any]:
        """Get information about a specific vulnerability session"""
        try:
            db = MongoDBConnection.get_database()
            collection = db.vulnerability_sessions
            
            session = await collection.find_one({"session_id": session_id})
            if session:
                return {
                    "session_id": session["session_id"],
                    "created_at": session["created_at"],
                    "total_vulnerabilities": len(session.get("vulnerabilities", [])),
                    "business_impact": session.get("business_impact", "Medium"),
                    "source": session.get("source", "NVD Service")
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching session info: {e}")
            return {}
