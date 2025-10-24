"""
Enhanced Risk Analysis Service with AVOID/MITIGATE/TRANSFER/ACCEPT Rubric
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class RiskMitigationStrategy(str, Enum):
    """Risk mitigation strategy enumeration"""
    AVOID = "AVOID"
    MITIGATE = "MITIGATE" 
    TRANSFER = "TRANSFER"
    ACCEPT = "ACCEPT"

class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class EnhancedRiskAnalysisService:
    """Enhanced risk analysis service with detailed mitigation strategies"""
    
    def __init__(self):
        # Vulnerability patterns and their risk levels
        self.vulnerability_patterns = {
            VulnerabilitySeverity.CRITICAL: [
                "remote code execution", "rce", "privilege escalation", "root access",
                "arbitrary code execution", "unauthenticated", "authentication bypass",
                "buffer overflow", "memory corruption", "zero day", "critical",
                "command injection", "code injection", "deserialization"
            ],
            VulnerabilitySeverity.HIGH: [
                "sql injection", "directory traversal", "path traversal", "file inclusion",
                "denial of service", "dos", "ddos", "high", "injection",
                "cross-site scripting", "xss", "csrf", "session fixation"
            ],
            VulnerabilitySeverity.MEDIUM: [
                "information disclosure", "medium", "weak encryption", "insecure storage",
                "information leakage", "security misconfiguration", "weak authentication",
                "insufficient access control", "crypto weakness"
            ],
            VulnerabilitySeverity.LOW: [
                "low", "minor", "limited impact", "weak password", "insufficient logging",
                "improper input validation", "verbose error messages"
            ],
            VulnerabilitySeverity.INFO: [
                "informational", "info", "deprecated", "cosmetic", "documentation",
                "version disclosure", "banner disclosure"
            ]
        }
        
        # Service-specific risk assessments
        self.service_risk_profiles = {
            "ssh": {"base_risk": 6.0, "critical_ports": [22]},
            "http": {"base_risk": 4.0, "critical_ports": [80, 443]},
            "https": {"base_risk": 3.0, "critical_ports": [443]},
            "ftp": {"base_risk": 7.0, "critical_ports": [21]},
            "telnet": {"base_risk": 8.0, "critical_ports": [23]},
            "mysql": {"base_risk": 6.0, "critical_ports": [3306]},
            "postgresql": {"base_risk": 6.0, "critical_ports": [5432]},
            "mongodb": {"base_risk": 6.0, "critical_ports": [27017]},
            "redis": {"base_risk": 7.0, "critical_ports": [6379]},
            "smb": {"base_risk": 7.0, "critical_ports": [445, 139]},
            "rdp": {"base_risk": 6.0, "critical_ports": [3389]},
            "vnc": {"base_risk": 8.0, "critical_ports": [5900, 5901]},
            "snmp": {"base_risk": 5.0, "critical_ports": [161]},
            "ldap": {"base_risk": 5.0, "critical_ports": [389, 636]},
            "dns": {"base_risk": 3.0, "critical_ports": [53]},
            "dhcp": {"base_risk": 4.0, "critical_ports": [67, 68]},
            "ntp": {"base_risk": 2.0, "critical_ports": [123]},
            "unknown": {"base_risk": 5.0, "critical_ports": []}
        }
        
        # Risk mitigation strategies database
        self.mitigation_strategies = {
            VulnerabilitySeverity.CRITICAL: {
                RiskMitigationStrategy.AVOID: {
                    "description": "Eliminar o aislar completamente el activo",
                    "conditions": ["RCE vulnerabilities", "Authentication bypass", "Privilege escalation"],
                    "actions": [
                        "Desconectar inmediatamente el servicio de la red",
                        "Aislar el sistema en una VLAN separada",
                        "Considerar reemplazo completo del software/hardware",
                        "Implementar controles de acceso físico estrictos"
                    ],
                    "technical_details": "Para vulnerabilidades críticas como RCE, el riesgo de compromiso total del sistema es inaceptable. La eliminación física o el aislamiento completo son las únicas medidas efectivas."
                },
                RiskMitigationStrategy.MITIGATE: {
                    "description": "Aplicar parches críticos y controles de seguridad",
                    "conditions": ["Patches disponibles", "Sistema crítico para operaciones"],
                    "actions": [
                        "Aplicar parches de seguridad inmediatamente",
                        "Implementar WAF (Web Application Firewall)",
                        "Configurar IPS/IDS específico para la vulnerabilidad",
                        "Endurecer configuraciones de seguridad",
                        "Implementar monitoreo 24/7"
                    ],
                    "technical_details": "Si el sistema es crítico y hay parches disponibles, aplicar inmediatamente con testing en ambiente controlado. Implementar múltiples capas de defensa."
                },
                RiskMitigationStrategy.TRANSFER: {
                    "description": "Externalizar el riesgo mediante seguros o servicios especializados",
                    "conditions": ["Sistema no crítico", "Costo de mitigación muy alto"],
                    "actions": [
                        "Contratar seguro de ciberseguridad específico",
                        "Externalizar gestión a MSSP especializado",
                        "Implementar SOC-as-a-Service",
                        "Contratar servicios de respuesta a incidentes"
                    ],
                    "technical_details": "Para sistemas no críticos donde el costo de mitigación excede el valor del activo, transferir el riesgo financiero y operacional."
                }
            },
            VulnerabilitySeverity.HIGH: {
                RiskMitigationStrategy.MITIGATE: {
                    "description": "Aplicar parches y controles de seguridad específicos",
                    "conditions": ["Vulnerabilidades de inyección", "Servicios expuestos"],
                    "actions": [
                        "Aplicar parches de seguridad prioritarios",
                        "Implementar validación de entrada estricta",
                        "Configurar firewalls de aplicación",
                        "Implementar autenticación multifactor",
                        "Cerrar puertos innecesarios"
                    ],
                    "technical_details": "Para vulnerabilidades HIGH como SQL injection, implementar validación de entrada, prepared statements, y WAF con reglas específicas."
                },
                RiskMitigationStrategy.TRANSFER: {
                    "description": "Externalizar gestión de seguridad específica",
                    "conditions": ["Servicios legacy", "Recursos internos limitados"],
                    "actions": [
                        "Contratar servicios de gestión de vulnerabilidades",
                        "Externalizar monitoreo de seguridad",
                        "Implementar servicios de backup y recuperación"
                    ],
                    "technical_details": "Para sistemas legacy complejos, externalizar la gestión especializada puede ser más efectivo que intentar mitigación interna."
                }
            },
            VulnerabilitySeverity.MEDIUM: {
                RiskMitigationStrategy.MITIGATE: {
                    "description": "Implementar controles de seguridad estándar",
                    "conditions": ["Configuraciones inseguras", "Información sensible expuesta"],
                    "actions": [
                        "Endurecer configuraciones por defecto",
                        "Implementar cifrado en tránsito y reposo",
                        "Configurar logging y monitoreo",
                        "Aplicar principio de menor privilegio",
                        "Implementar rotación de credenciales"
                    ],
                    "technical_details": "Para vulnerabilidades MEDIUM, enfocarse en hardening estándar y controles de seguridad básicos que reducen significativamente el riesgo."
                },
                RiskMitigationStrategy.ACCEPT: {
                    "description": "Documentar y monitorear riesgos controlados",
                    "conditions": ["Riesgo bajo impacto", "Mitigación costosa"],
                    "actions": [
                        "Documentar riesgo en registro de riesgos",
                        "Implementar monitoreo continuo",
                        "Establecer umbrales de alerta",
                        "Revisar periódicamente la aceptabilidad"
                    ],
                    "technical_details": "Para vulnerabilidades MEDIUM con bajo impacto de negocio, documentar y monitorear puede ser más eficiente que mitigación completa."
                }
            },
            VulnerabilitySeverity.LOW: {
                RiskMitigationStrategy.ACCEPT: {
                    "description": "Monitorear y documentar riesgos menores",
                    "conditions": ["Impacto mínimo", "Costo de mitigación alto"],
                    "actions": [
                        "Documentar en registro de riesgos",
                        "Implementar monitoreo básico",
                        "Revisar en próximos ciclos de evaluación",
                        "Considerar mitigación en futuras actualizaciones"
                    ],
                    "technical_details": "Para vulnerabilidades LOW, el costo de mitigación generalmente excede el beneficio. Monitorear y documentar es la estrategia más eficiente."
                },
                RiskMitigationStrategy.MITIGATE: {
                    "description": "Aplicar controles básicos de seguridad",
                    "conditions": ["Mitigación simple disponible", "Cumplimiento requerido"],
                    "actions": [
                        "Aplicar parches menores cuando disponibles",
                        "Configurar logging básico",
                        "Implementar controles de acceso básicos"
                    ],
                    "technical_details": "Si la mitigación es simple y económica, aplicarla para mejorar la postura general de seguridad."
                }
            }
        }

    def analyze_nmap_results(self, nmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze nmap scan results and provide detailed risk assessment with mitigation strategies
        """
        logger.info(f"Analyzing nmap results for target: {nmap_data.get('ip', 'unknown')}")
        
        analysis_result = {
            "target": nmap_data.get("ip", "unknown"),
            "os": nmap_data.get("os", "Unknown"),
            "status": nmap_data.get("status", "unknown"),
            "scan_timestamp": datetime.now().isoformat(),
            "services": [],
            "vulnerabilities": [],
            "risk_assessment": {},
            "recommendations": []
        }
        
        # Analyze each service
        services = nmap_data.get("services", [])
        total_risk_score = 0.0
        critical_services = 0
        high_risk_services = 0
        
        for service in services:
            service_analysis = self._analyze_service(service)
            analysis_result["services"].append(service_analysis)
            
            total_risk_score += service_analysis["risk_score"]
            if service_analysis["risk_level"] == VulnerabilitySeverity.CRITICAL:
                critical_services += 1
            elif service_analysis["risk_level"] == VulnerabilitySeverity.HIGH:
                high_risk_services += 1
        
        # Analyze vulnerabilities
        vulnerabilities = nmap_data.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            vuln_analysis = self._analyze_vulnerability(vuln)
            analysis_result["vulnerabilities"].append(vuln_analysis)
        
        # Calculate overall risk assessment
        avg_risk_score = total_risk_score / len(services) if services else 0.0
        analysis_result["risk_assessment"] = self._calculate_overall_risk(
            avg_risk_score, critical_services, high_risk_services, len(services)
        )
        
        # Generate specific recommendations
        analysis_result["recommendations"] = self._generate_recommendations(
            analysis_result["services"], analysis_result["vulnerabilities"], 
            analysis_result["risk_assessment"]
        )
        
        return analysis_result

    def _analyze_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual service for risk"""
        port = service.get("port", "unknown")
        service_name = service.get("name", "unknown").lower()
        product = service.get("product", "").lower()
        version = service.get("version", "")
        
        # Get base risk profile
        risk_profile = self.service_risk_profiles.get(service_name, self.service_risk_profiles["unknown"])
        base_risk = risk_profile["base_risk"]
        
        # Adjust risk based on version disclosure
        if version:
            base_risk += 1.0  # Version disclosure increases risk
        
        # Adjust risk based on port
        if port in risk_profile["critical_ports"]:
            base_risk += 0.5
        
        # Determine risk level
        if base_risk >= 7.5:
            risk_level = VulnerabilitySeverity.CRITICAL
        elif base_risk >= 6.0:
            risk_level = VulnerabilitySeverity.HIGH
        elif base_risk >= 4.0:
            risk_level = VulnerabilitySeverity.MEDIUM
        elif base_risk >= 2.0:
            risk_level = VulnerabilitySeverity.LOW
        else:
            risk_level = VulnerabilitySeverity.INFO
        
        # Generate mitigation strategy
        mitigation = self._get_mitigation_strategy(risk_level, service_name, port)
        
        return {
            "port": port,
            "protocol": service.get("protocol", "tcp"),
            "service_name": service_name,
            "product": product,
            "version": version,
            "state": service.get("state", "unknown"),
            "risk_score": base_risk,
            "risk_level": risk_level,
            "mitigation_strategy": mitigation,
            "technical_details": self._get_service_technical_details(service_name, port, version)
        }

    def _analyze_vulnerability(self, vuln: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual vulnerability"""
        vuln_id = vuln.get("id", "unknown")
        output = vuln.get("output", "").lower()
        
        # Determine severity based on output content
        severity = VulnerabilitySeverity.INFO
        for sev_level, patterns in self.vulnerability_patterns.items():
            if any(pattern in output for pattern in patterns):
                severity = sev_level
                break
        
        # Get mitigation strategy
        mitigation = self._get_mitigation_strategy(severity, vuln_id, None)
        
        return {
            "id": vuln_id,
            "output": vuln.get("output", ""),
            "severity": severity,
            "mitigation_strategy": mitigation,
            "technical_details": self._get_vulnerability_technical_details(vuln_id, output, severity)
        }

    def _get_mitigation_strategy(self, severity: VulnerabilitySeverity, context: str, port: Optional[str]) -> Dict[str, Any]:
        """Get appropriate mitigation strategy based on severity and context"""
        strategies = self.mitigation_strategies.get(severity, {})
        
        # Select best strategy based on context
        if severity == VulnerabilitySeverity.CRITICAL:
            # For critical vulnerabilities, prefer AVOID or MITIGATE
            if "rce" in context.lower() or "remote code execution" in context.lower():
                return strategies.get(RiskMitigationStrategy.AVOID, strategies.get(RiskMitigationStrategy.MITIGATE, {}))
            else:
                return strategies.get(RiskMitigationStrategy.MITIGATE, strategies.get(RiskMitigationStrategy.AVOID, {}))
        elif severity == VulnerabilitySeverity.HIGH:
            return strategies.get(RiskMitigationStrategy.MITIGATE, strategies.get(RiskMitigationStrategy.TRANSFER, {}))
        elif severity == VulnerabilitySeverity.MEDIUM:
            return strategies.get(RiskMitigationStrategy.MITIGATE, strategies.get(RiskMitigationStrategy.ACCEPT, {}))
        else:
            return strategies.get(RiskMitigationStrategy.ACCEPT, strategies.get(RiskMitigationStrategy.MITIGATE, {}))

    def _get_service_technical_details(self, service_name: str, port: str, version: str) -> str:
        """Generate technical details for service analysis"""
        details = []
        
        if service_name == "ssh":
            details.append("SSH es un protocolo crítico para administración remota. Vulnerabilidades pueden permitir acceso completo al sistema.")
            if version:
                details.append(f"Versión detectada: {version}. Verificar si hay vulnerabilidades conocidas para esta versión.")
            details.append("Recomendaciones: Deshabilitar autenticación por contraseña, usar solo claves SSH, implementar fail2ban.")
        
        elif service_name in ["http", "https"]:
            details.append("Servicios web son objetivos comunes de ataques. Vulnerabilidades pueden comprometer aplicaciones y datos.")
            details.append("Recomendaciones: Implementar WAF, mantener certificados SSL actualizados, usar headers de seguridad.")
        
        elif service_name in ["mysql", "postgresql", "mongodb", "redis"]:
            details.append("Bases de datos contienen información sensible. Acceso no autorizado puede comprometer datos críticos.")
            details.append("Recomendaciones: Restringir acceso por IP, usar autenticación fuerte, cifrar datos en reposo.")
        
        elif service_name == "ftp":
            details.append("FTP es un protocolo inseguro que transmite credenciales en texto plano.")
            details.append("Recomendaciones: Migrar a SFTP o FTPS, o considerar eliminación si no es esencial.")
        
        elif service_name == "telnet":
            details.append("Telnet es extremadamente inseguro, transmite todo en texto plano.")
            details.append("Recomendaciones: Eliminar inmediatamente y migrar a SSH.")
        
        else:
            details.append(f"Servicio {service_name} en puerto {port} requiere análisis específico de seguridad.")
            if version:
                details.append(f"Verificar vulnerabilidades conocidas para {service_name} versión {version}.")
        
        return " ".join(details)

    def _get_vulnerability_technical_details(self, vuln_id: str, output: str, severity: VulnerabilitySeverity) -> str:
        """Generate technical details for vulnerability analysis"""
        details = []
        
        if "sql injection" in output:
            details.append("SQL Injection permite ejecutar consultas SQL maliciosas. Puede resultar en acceso a datos, modificación o eliminación.")
            details.append("Impacto técnico: Bypass de autenticación, acceso a información sensible, escalación de privilegios.")
        
        elif "remote code execution" in output or "rce" in output:
            details.append("Remote Code Execution permite ejecutar código arbitrario en el servidor remoto.")
            details.append("Impacto técnico: Compromiso completo del sistema, acceso a datos, instalación de malware.")
        
        elif "buffer overflow" in output:
            details.append("Buffer Overflow puede causar corrupción de memoria y ejecución de código malicioso.")
            details.append("Impacto técnico: Crash de aplicación, ejecución de código, escalación de privilegios.")
        
        elif "cross-site scripting" in output or "xss" in output:
            details.append("Cross-Site Scripting permite ejecutar JavaScript malicioso en el navegador del usuario.")
            details.append("Impacto técnico: Robo de sesiones, redirección maliciosa, robo de datos del usuario.")
        
        elif "denial of service" in output or "dos" in output:
            details.append("Denial of Service puede hacer que el servicio no esté disponible para usuarios legítimos.")
            details.append("Impacto técnico: Indisponibilidad del servicio, pérdida de productividad.")
        
        else:
            details.append(f"Vulnerabilidad {vuln_id} requiere análisis específico basado en el contexto de la aplicación.")
            details.append(f"Severidad: {severity.value}. Revisar detalles específicos en la base de datos de vulnerabilidades.")
        
        return " ".join(details)

    def _calculate_overall_risk(self, avg_risk_score: float, critical_services: int, high_risk_services: int, total_services: int) -> Dict[str, Any]:
        """Calculate overall risk assessment"""
        if avg_risk_score >= 7.0 or critical_services > 0:
            overall_level = "CRITICAL"
        elif avg_risk_score >= 5.0 or high_risk_services > total_services * 0.3:
            overall_level = "HIGH"
        elif avg_risk_score >= 3.0:
            overall_level = "MEDIUM"
        else:
            overall_level = "LOW"
        
        return {
            "overall_level": overall_level,
            "average_risk_score": avg_risk_score,
            "critical_services_count": critical_services,
            "high_risk_services_count": high_risk_services,
            "total_services": total_services,
            "risk_factors": {
                "exposed_services": total_services,
                "version_disclosure": "Detected" if avg_risk_score > 4.0 else "Minimal",
                "critical_services_ratio": critical_services / total_services if total_services > 0 else 0
            }
        }

    def _generate_recommendations(self, services: List[Dict], vulnerabilities: List[Dict], risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        # Overall risk recommendations
        overall_level = risk_assessment["overall_level"]
        
        if overall_level == "CRITICAL":
            recommendations.append({
                "priority": "IMMEDIATE",
                "category": "Emergency Response",
                "title": "Acción Inmediata Requerida",
                "description": "El sistema presenta riesgos críticos que requieren acción inmediata",
                "actions": [
                    "Desconectar servicios críticos de la red pública",
                    "Aislar el sistema en una VLAN separada",
                    "Notificar al equipo de seguridad",
                    "Iniciar proceso de respuesta a incidentes"
                ],
                "technical_rationale": "La presencia de servicios críticos expuestos representa un riesgo inaceptable de compromiso total del sistema."
            })
        
        # Service-specific recommendations
        for service in services:
            if service["risk_level"] in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]:
                mitigation = service["mitigation_strategy"]
                recommendations.append({
                    "priority": "HIGH" if service["risk_level"] == VulnerabilitySeverity.CRITICAL else "MEDIUM",
                    "category": f"Service Security - {service['service_name'].upper()}",
                    "title": f"Securizar servicio {service['service_name']} en puerto {service['port']}",
                    "description": mitigation.get("description", "Implementar controles de seguridad"),
                    "actions": mitigation.get("actions", []),
                    "technical_rationale": mitigation.get("technical_details", "Servicio presenta riesgos de seguridad significativos")
                })
        
        # Vulnerability-specific recommendations
        for vuln in vulnerabilities:
            if vuln["severity"] in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]:
                mitigation = vuln["mitigation_strategy"]
                recommendations.append({
                    "priority": "HIGH" if vuln["severity"] == VulnerabilitySeverity.CRITICAL else "MEDIUM",
                    "category": f"Vulnerability - {vuln['id']}",
                    "title": f"Mitigar vulnerabilidad {vuln['id']}",
                    "description": mitigation.get("description", "Aplicar medidas de mitigación"),
                    "actions": mitigation.get("actions", []),
                    "technical_rationale": mitigation.get("technical_details", "Vulnerabilidad presenta riesgo significativo")
                })
        
        return recommendations

