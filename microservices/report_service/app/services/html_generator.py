import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Template
from app.api.schemas import VulnerabilityData, ReportMetrics, ReportType
import logging

logger = logging.getLogger(__name__)

class HTMLReportGenerator:
    """Generate HTML reports from vulnerability data"""
    
    def __init__(self, temp_dir: str = "/tmp/reports"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def generate_vulnerability_summary(self, 
                                     vulnerabilities: List[VulnerabilityData],
                                     metrics: ReportMetrics,
                                     session_info: Dict[str, Any] = None) -> str:
        """Generate a comprehensive vulnerability summary HTML report"""
        
        report_id = str(uuid.uuid4())
        filename = f"vulnerability_summary_{report_id}.html"
        filepath = os.path.join(self.temp_dir, filename)
        
        # Prepare data for template
        template_data = {
            'title': 'Vulnerability Assessment Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': metrics,
            'session_info': session_info or {},
            'vulnerabilities': vulnerabilities,
            'critical_high_vulns': [v for v in vulnerabilities if v.severity in ['CRITICAL', 'HIGH']],
            'recommendations': self._generate_recommendations(metrics, vulnerabilities)
        }
        
        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
        }
        h2 {
            color: #e74c3c;
            border-left: 4px solid #e74c3c;
            padding-left: 15px;
            margin-top: 30px;
        }
        h3 {
            color: #34495e;
        }
        .summary-box {
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background-color: #3498db;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-card.critical { background-color: #e74c3c; }
        .metric-card.high { background-color: #f39c12; }
        .metric-card.medium { background-color: #f1c40f; color: #2c3e50; }
        .metric-card.low { background-color: #27ae60; }
        .metric-number {
            font-size: 2.5em;
            font-weight: bold;
        }
        .metric-label {
            font-size: 0.9em;
            margin-top: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #34495e;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .severity-critical {
            background-color: #e74c3c;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .severity-high {
            background-color: #f39c12;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .severity-medium {
            background-color: #f1c40f;
            color: #2c3e50;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .severity-low {
            background-color: #27ae60;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .vulnerability-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            background-color: #fafafa;
        }
        .vulnerability-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .cve-id {
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.2em;
        }
        .score {
            font-weight: bold;
            font-size: 1.1em;
        }
        .recommendations {
            background-color: #d5f4e6;
            border-left: 4px solid #27ae60;
            padding: 20px;
            margin: 20px 0;
        }
        .recommendations ul {
            margin: 0;
            padding-left: 20px;
        }
        .recommendations li {
            margin: 10px 0;
        }
        .session-info {
            background-color: #e8f4fd;
            border: 1px solid #3498db;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        .chart-placeholder {
            background-color: #ecf0f1;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            margin: 20px 0;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        
        <div class="summary-box">
            <h3>Executive Summary</h3>
            <p>This report provides a comprehensive analysis of <strong>{{ metrics.total_vulnerabilities }}</strong> vulnerabilities 
            identified in the system. The average CVSS score is <strong>{{ "%.2f"|format(metrics.average_score) }}</strong>, indicating 
            {% if metrics.average_score >= 7.0 %}
                <strong style="color: #e74c3c;">high</strong>
            {% elif metrics.average_score >= 4.0 %}
                <strong style="color: #f39c12;">medium</strong>
            {% else %}
                <strong style="color: #27ae60;">low</strong>
            {% endif %}
            overall risk level.</p>
            
            {% if session_info %}
            <div class="session-info">
                <strong>Analysis Details:</strong><br>
                Session ID: {{ session_info.session_id or 'N/A' }}<br>
                Generated: {{ generated_at }}<br>
                Business Impact: {{ session_info.business_impact or 'Medium' }}<br>
                Data Source: {{ session_info.source or 'NVD Service' }}
            </div>
            {% endif %}
        </div>

        <h2>Key Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-number">{{ metrics.total_vulnerabilities }}</div>
                <div class="metric-label">Total Vulnerabilities</div>
            </div>
            <div class="metric-card critical">
                <div class="metric-number">{{ metrics.critical_count }}</div>
                <div class="metric-label">Critical</div>
            </div>
            <div class="metric-card high">
                <div class="metric-number">{{ metrics.high_count }}</div>
                <div class="metric-label">High</div>
            </div>
            <div class="metric-card medium">
                <div class="metric-number">{{ metrics.medium_count }}</div>
                <div class="metric-label">Medium</div>
            </div>
            <div class="metric-card low">
                <div class="metric-number">{{ metrics.low_count }}</div>
                <div class="metric-label">Low</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{{ "%.1f"|format(metrics.average_score) }}</div>
                <div class="metric-label">Average CVSS Score</div>
            </div>
        </div>

        <h2>Risk Distribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Risk Level</th>
                    <th>Score Range</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="severity-critical">Critical</span></td>
                    <td>9.0 - 10.0</td>
                    <td>{{ metrics.risk_distribution.get('Critical (9.0-10.0)', 0) }}</td>
                    <td>{{ "%.1f"|format((metrics.risk_distribution.get('Critical (9.0-10.0)', 0) / metrics.total_vulnerabilities * 100) if metrics.total_vulnerabilities > 0 else 0) }}%</td>
                </tr>
                <tr>
                    <td><span class="severity-high">High</span></td>
                    <td>7.0 - 8.9</td>
                    <td>{{ metrics.risk_distribution.get('High (7.0-8.9)', 0) }}</td>
                    <td>{{ "%.1f"|format((metrics.risk_distribution.get('High (7.0-8.9)', 0) / metrics.total_vulnerabilities * 100) if metrics.total_vulnerabilities > 0 else 0) }}%</td>
                </tr>
                <tr>
                    <td><span class="severity-medium">Medium</span></td>
                    <td>4.0 - 6.9</td>
                    <td>{{ metrics.risk_distribution.get('Medium (4.0-6.9)', 0) }}</td>
                    <td>{{ "%.1f"|format((metrics.risk_distribution.get('Medium (4.0-6.9)', 0) / metrics.total_vulnerabilities * 100) if metrics.total_vulnerabilities > 0 else 0) }}%</td>
                </tr>
                <tr>
                    <td><span class="severity-low">Low</span></td>
                    <td>0.1 - 3.9</td>
                    <td>{{ metrics.risk_distribution.get('Low (0.1-3.9)', 0) }}</td>
                    <td>{{ "%.1f"|format((metrics.risk_distribution.get('Low (0.1-3.9)', 0) / metrics.total_vulnerabilities * 100) if metrics.total_vulnerabilities > 0 else 0) }}%</td>
                </tr>
                <tr>
                    <td>None</td>
                    <td>0.0</td>
                    <td>{{ metrics.risk_distribution.get('None (0.0)', 0) }}</td>
                    <td>{{ "%.1f"|format((metrics.risk_distribution.get('None (0.0)', 0) / metrics.total_vulnerabilities * 100) if metrics.total_vulnerabilities > 0 else 0) }}%</td>
                </tr>
            </tbody>
        </table>

        {% if critical_high_vulns %}
        <h2>Critical and High Severity Vulnerabilities</h2>
        {% for vuln in critical_high_vulns[:10] %}
        <div class="vulnerability-card">
            <div class="vulnerability-header">
                <span class="cve-id">{{ vuln.cve_id }}</span>
                <span class="severity-{{ vuln.severity.lower() }}">{{ vuln.severity }}</span>
                <span class="score">{{ vuln.score }}</span>
            </div>
            <p><strong>Published:</strong> {{ vuln.published_date.strftime('%Y-%m-%d') }}</p>
            <p><strong>Description:</strong> {{ vuln.description }}</p>
            {% if vuln.affected_products %}
            <p><strong>Affected Products:</strong> {{ vuln.affected_products[:3]|join(', ') }}</p>
            {% endif %}
            {% if vuln.business_impact %}
            <p><strong>Business Impact:</strong> {{ vuln.business_impact }}</p>
            {% endif %}
        </div>
        {% endfor %}
        {% else %}
        <h2>Critical and High Severity Vulnerabilities</h2>
        <p>No critical or high severity vulnerabilities found.</p>
        {% endif %}

        <div class="recommendations">
            <h2>Recommendations</h2>
            <ul>
                {% for rec in recommendations %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 50px; color: #7f8c8d; font-size: 0.9em;">
            Report generated on {{ generated_at }} by Risk Management System
        </div>
    </div>
</body>
</html>
        """
        
        # Render template
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {filepath}")
        return filename
    
    def _generate_recommendations(self, metrics: ReportMetrics, vulnerabilities: List[VulnerabilityData]) -> List[str]:
        """Generate recommendations based on vulnerability data"""
        recommendations = []
        
        if metrics.critical_count > 0:
            recommendations.append(f"Immediately address {metrics.critical_count} critical vulnerabilities with CVSS scores ≥ 9.0")
        
        if metrics.high_count > 0:
            recommendations.append(f"Prioritize remediation of {metrics.high_count} high severity vulnerabilities")
        
        if metrics.average_score >= 7.0:
            recommendations.append("Overall risk level is HIGH - implement emergency patching procedures")
        elif metrics.average_score >= 4.0:
            recommendations.append("Overall risk level is MEDIUM - schedule regular patching cycles")
        else:
            recommendations.append("Overall risk level is LOW - maintain current security posture")
        
        # Product-specific recommendations
        affected_products = set()
        for vuln in vulnerabilities:
            affected_products.update(vuln.affected_products)
        
        if len(affected_products) > 10:
            recommendations.append("Large number of affected products detected - conduct comprehensive asset inventory")
        
        if metrics.total_vulnerabilities > 100:
            recommendations.append("High volume of vulnerabilities - consider automated vulnerability management tools")
        
        recommendations.extend([
            "Implement regular vulnerability scanning and assessment procedures",
            "Establish a vulnerability management program with defined SLAs",
            "Consider penetration testing for critical systems",
            "Ensure all systems are covered by security monitoring"
        ])
        
        return recommendations
