import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from app.api.schemas import VulnerabilityData, ReportMetrics, ReportType
import logging

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """Generate PDF reports from vulnerability data"""
    
    def __init__(self, temp_dir: str = "/tmp/reports"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkred
        ))
    
    def generate_vulnerability_summary(self, 
                                     vulnerabilities: List[VulnerabilityData],
                                     metrics: ReportMetrics,
                                     session_info: Dict[str, Any] = None) -> str:
        """Generate a comprehensive vulnerability summary PDF report"""
        
        report_id = str(uuid.uuid4())
        filename = f"vulnerability_summary_{report_id}.pdf"
        filepath = os.path.join(self.temp_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=inch)
        story = []
        
        # Title
        story.append(Paragraph("Vulnerability Assessment Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        summary_text = f"""
        This report provides a comprehensive analysis of {metrics.total_vulnerabilities} vulnerabilities 
        identified in the system. The average CVSS score is {metrics.average_score:.2f}, indicating 
        {"high" if metrics.average_score >= 7.0 else "medium" if metrics.average_score >= 4.0 else "low"} 
        overall risk level.
        """
        
        if session_info:
            summary_text += f"""
            <br/><br/>
            <b>Analysis Details:</b><br/>
            Session ID: {session_info.get('session_id', 'N/A')}<br/>
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            Business Impact: {session_info.get('business_impact', 'Medium')}<br/>
            Data Source: {session_info.get('source', 'NVD Service')}
            """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Vulnerability Distribution
        story.append(Paragraph("Vulnerability Distribution by Severity", self.styles['SectionHeader']))
        
        # Create distribution table
        severity_data = [
            ['Severity Level', 'Count', 'Percentage'],
            ['Critical', str(metrics.critical_count), f"{(metrics.critical_count/metrics.total_vulnerabilities*100):.1f}%" if metrics.total_vulnerabilities > 0 else "0%"],
            ['High', str(metrics.high_count), f"{(metrics.high_count/metrics.total_vulnerabilities*100):.1f}%" if metrics.total_vulnerabilities > 0 else "0%"],
            ['Medium', str(metrics.medium_count), f"{(metrics.medium_count/metrics.total_vulnerabilities*100):.1f}%" if metrics.total_vulnerabilities > 0 else "0%"],
            ['Low', str(metrics.low_count), f"{(metrics.low_count/metrics.total_vulnerabilities*100):.1f}%" if metrics.total_vulnerabilities > 0 else "0%"]
        ]
        
        severity_table = Table(severity_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        severity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(severity_table)
        story.append(Spacer(1, 30))
        
        # Risk Distribution Chart (simplified)
        story.append(Paragraph("Risk Score Distribution", self.styles['SectionHeader']))
        
        risk_data = [
            ['Risk Level', 'Score Range', 'Count'],
            ['Critical', '9.0 - 10.0', str(metrics.risk_distribution.get('Critical (9.0-10.0)', 0))],
            ['High', '7.0 - 8.9', str(metrics.risk_distribution.get('High (7.0-8.9)', 0))],
            ['Medium', '4.0 - 6.9', str(metrics.risk_distribution.get('Medium (4.0-6.9)', 0))],
            ['Low', '0.1 - 3.9', str(metrics.risk_distribution.get('Low (0.1-3.9)', 0))],
            ['None', '0.0', str(metrics.risk_distribution.get('None (0.0)', 0))]
        ]
        
        risk_table = Table(risk_data, colWidths=[1.5*inch, 1.5*inch, 1*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(risk_table)
        story.append(PageBreak())
        
        # Top Vulnerabilities
        story.append(Paragraph("Critical and High Severity Vulnerabilities", self.styles['SectionHeader']))
        
        # Filter and sort vulnerabilities by severity and score
        critical_high_vulns = [v for v in vulnerabilities if v.severity in ['CRITICAL', 'HIGH']]
        critical_high_vulns.sort(key=lambda x: x.score, reverse=True)
        
        if critical_high_vulns:
            for i, vuln in enumerate(critical_high_vulns[:10]):  # Top 10
                story.append(Paragraph(f"<b>{i+1}. {vuln.cve_id}</b>", self.styles['Heading3']))
                
                vuln_details = f"""
                <b>Severity:</b> {vuln.severity}<br/>
                <b>CVSS Score:</b> {vuln.score}<br/>
                <b>Published:</b> {vuln.published_date.strftime('%Y-%m-%d')}<br/>
                <b>Description:</b> {vuln.description}<br/>
                """
                
                if vuln.affected_products:
                    vuln_details += f"<b>Affected Products:</b> {', '.join(vuln.affected_products[:3])}<br/>"
                
                if vuln.business_impact:
                    vuln_details += f"<b>Business Impact:</b> {vuln.business_impact}<br/>"
                
                story.append(Paragraph(vuln_details, self.styles['Normal']))
                story.append(Spacer(1, 15))
        else:
            story.append(Paragraph("No critical or high severity vulnerabilities found.", self.styles['Normal']))
        
        story.append(PageBreak())
        
        # Recommendations
        story.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        
        recommendations = self._generate_recommendations(metrics, vulnerabilities)
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['Normal']))
            story.append(Spacer(1, 8))
        
        # Build PDF
        doc.build(story)
        logger.info(f"Generated PDF report: {filepath}")
        
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
