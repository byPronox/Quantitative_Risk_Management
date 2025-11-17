import React, { useState, useEffect } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './GeneralReports.css';

const GeneralReports = () => {
  const [keywords, setKeywords] = useState([]);
  const [filteredKeywords, setFilteredKeywords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  const [detailedReport, setDetailedReport] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch keywords summary on component mount
  useEffect(() => {
    fetchKeywordsSummary();
  }, []);

  // Filter keywords when search term changes
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredKeywords(keywords);
    } else {
      const filtered = keywords.filter(keywordData =>
        keywordData.keyword.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredKeywords(filtered);
    }
  }, [keywords, searchTerm]);

  const fetchKeywordsSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/reports/general/keywords');
      const data = await response.json();
      
      if (data.success) {
        setKeywords(data.keywords);
        setFilteredKeywords(data.keywords);
      } else {
        console.error('Error fetching keywords:', data.error);
      }
    } catch (error) {
      console.error('Error fetching keywords summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetailedReport = async (keyword) => {
    try {
      setLoadingDetails(true);
      setSelectedKeyword(keyword);
      
      const response = await fetch(`http://localhost:8000/reports/general/keyword/${encodeURIComponent(keyword)}`);
      const data = await response.json();
      
      if (data.success) {
        setDetailedReport(data);
      } else {
        console.error('Error fetching detailed report:', data.error);
      }
    } catch (error) {
      console.error('Error fetching detailed report:', error);
    } finally {
      setLoadingDetails(false);
    }
  };

  const goBackToSummary = () => {
    setSelectedKeyword(null);
    setDetailedReport(null);
  };

  const downloadReportAsPDF = async () => {
    try {
      const reportElement = document.getElementById('detailed-report-content');
      if (!reportElement) {
        console.error('Report element not found');
        return;
      }

      // Create a clone of the element to modify for PDF
      const clonedElement = reportElement.cloneNode(true);
      clonedElement.style.width = '800px';
      clonedElement.style.backgroundColor = 'white';
      clonedElement.style.padding = '20px';
      
      // Append temporarily to body (hidden)
      clonedElement.style.position = 'absolute';
      clonedElement.style.left = '-9999px';
      document.body.appendChild(clonedElement);

      // Generate canvas from the cloned element
      const canvas = await html2canvas(clonedElement, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        width: 840,
        height: clonedElement.scrollHeight
      });

      // Remove the cloned element
      document.body.removeChild(clonedElement);

      // Create PDF
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      
      const imgWidth = 210; // A4 width in mm
      const pageHeight = 295; // A4 height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      // Add first page
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      // Add additional pages if needed
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      // Download the PDF
      pdf.save(`${selectedKeyword}_Reporte_Vulnerabilidades.pdf`);
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Error al generar PDF. Por favor intente de nuevo.');
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  if (loading) {    return (
      <div className="general-reports">
        <div className="loading">
          <div className="spinner"></div>
          <p>Cargando Reportes Generales...</p>
        </div>
      </div>
    );
  }

  if (selectedKeyword && detailedReport) {
    return (
      <div className="general-reports">        <div className="report-header">
          <button className="back-button" onClick={goBackToSummary}>
            ← Volver al Resumen
          </button>
          <h2>Reporte Detallado: {selectedKeyword}</h2>
          <button className="download-button" onClick={downloadReportAsPDF}>
            📄 Descargar Reporte
          </button>
        </div>

        {loadingDetails ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Cargando reporte detallado...</p>
          </div>
        ) : (
          <div className="detailed-report" id="detailed-report-content">
            {/* Summary Cards */}            <div className="summary-cards">
              <div className="summary-card">
                <h3>Total de Análisis</h3>
                <p className="metric">{detailedReport.total_jobs}</p>
              </div>
              <div className="summary-card">
                <h3>Total de Vulnerabilidades</h3>
                <p className="metric">{detailedReport.total_vulnerabilities}</p>
              </div>
              <div className="summary-card">
                <h3>Software</h3>
                <p className="metric">{selectedKeyword}</p>
              </div>
            </div>

            {/* Severity Distribution */}
            <div className="section">
              <h3>Distribución de Severidad</h3>
              <div className="severity-chart">
                {Object.entries(detailedReport.severity_distribution).map(([severity, count]) => (
                  count > 0 && (
                    <div key={severity} className="severity-item">
                      <div 
                        className="severity-bar"
                        style={{
                          backgroundColor: getSeverityColor(severity),
                          width: `${(count / detailedReport.total_vulnerabilities) * 100}%`
                        }}
                      >
                        <span className="severity-label">{severity}: {count}</span>
                      </div>
                    </div>
                  )
                ))}
              </div>
            </div>            {/* Vulnerabilities by Year */}
            <div className="section">
              <h3>Vulnerabilidades por Año</h3>
              <div className="year-distribution">
                {Object.entries(detailedReport.vulnerabilities_by_year).slice(0, 10).map(([year, count]) => (
                  <div key={year} className="year-item">
                    <span className="year">{year}</span>
                    <div className="year-bar">
                      <div 
                        className="year-fill"
                        style={{
                          width: `${(count / Math.max(...Object.values(detailedReport.vulnerabilities_by_year))) * 100}%`
                        }}
                      ></div>
                      <span className="year-count">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>            {/* Recent Vulnerabilities */}
            <div className="section">
              <h3>Vulnerabilidades Recientes (Top 10)</h3>
              <div className="vulnerabilities-table">
                <table>
                  <thead>
                    <tr>
                      <th>ID CVE</th>
                      <th>Severidad</th>
                      <th>Puntuación</th>
                      <th>Publicado</th>
                      <th>Descripción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailedReport.vulnerabilities.slice(0, 10).map((vuln, index) => {
                      const cve = vuln.cve || {};
                      const metrics = cve.metrics || {};
                      let severity = 'Desconocido';
                      let score = 'N/A';
                        if (metrics.cvssMetricV31 && metrics.cvssMetricV31.length > 0) {
                        severity = metrics.cvssMetricV31[0].cvssData?.baseSeverity || 'Desconocido';
                        score = metrics.cvssMetricV31[0].cvssData?.baseScore || 'N/A';
                      } else if (metrics.cvssMetricV2 && metrics.cvssMetricV2.length > 0) {
                        score = metrics.cvssMetricV2[0].cvssData?.baseScore || 'N/A';
                        if (score >= 9.0) severity = 'Crítico';
                        else if (score >= 7.0) severity = 'Alto';
                        else if (score >= 4.0) severity = 'Medio';
                        else severity = 'Bajo';
                      }

                      const description = cve.descriptions?.find(d => d.lang === 'en')?.value || 'Descripción no disponible';
                      
                      return (
                        <tr key={index}>
                          <td className="cve-id">{cve.id || 'N/A'}</td>
                          <td>
                            <span 
                              className="severity-badge"
                              style={{ backgroundColor: getSeverityColor(severity) }}
                            >
                              {severity}
                            </span>
                          </td>
                          <td className="score">{score}</td>
                          <td>{cve.published ? new Date(cve.published).toLocaleDateString() : 'N/A'}</td>
                          <td className="description">{description.substring(0, 100)}...</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>            {/* Analysis History */}
            <div className="section">
              <h3>Historial de Análisis</h3>
              <div className="jobs-history">
                {detailedReport.jobs.map((job, index) => (
                  <div key={index} className="job-item">
                    <div className="job-header">
                      <span className="job-id">Trabajo: {job.job_id}</span>
                      <span className="job-date">{job.processed_at_readable}</span>
                    </div>
                    <div className="job-stats">
                      <span>Resultados: {job.total_results}</span>
                      <span>Vulnerabilities: {job.vulnerabilities_count}</span>
                      <span className={`status ${job.status}`}>{job.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="general-reports">      <div className="header">
        <h2>Reportes Generales</h2>
        <p>Haga clic en cualquier software para ver el análisis detallado de vulnerabilidades</p>
      </div>

      {/* Search Filter */}
      <div className="search-section">
        <div className="search-container">
          <input
            type="text"
            placeholder="Buscar palabras clave (ej: Python, Node, Java...)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <div className="search-icon">🔍</div>
        </div>
        {searchTerm && (
          <div className="search-results-info">
            Mostrando {filteredKeywords.length} resultado(s) para "{searchTerm}"
          </div>
        )}
      </div>

      <div className="keywords-grid">
        {filteredKeywords.map((keywordData, index) => (
          <div 
            key={index} 
            className="keyword-card"
            onClick={() => fetchDetailedReport(keywordData.keyword)}
          >            <div className="keyword-header">
              <h3>{keywordData.keyword}</h3>
              <span className="vulnerability-count">{keywordData.total_vulnerabilities} vulnerabilidades</span>
            </div>
            <div className="keyword-stats">
              <div className="stat">
                <span className="label">Total de Análisis:</span>
                <span className="value">{keywordData.total_jobs}</span>
              </div>
              <div className="stat">
                <span className="label">Último Análisis:</span>
                <span className="value">{keywordData.latest_analysis}</span>
              </div>
            </div>
            <div className="jobs-preview">
              <h4>Trabajos Recientes:</h4>
              {keywordData.jobs.slice(0, 3).map((job, jobIndex) => (
                <div key={jobIndex} className="job-preview">
                  <span className="job-id">{job.job_id}</span>
                  <span className="job-vulns">{job.vulnerabilities_count} vulns</span>
                </div>
              ))}
              {keywordData.jobs.length > 3 && (
                <div className="more-jobs">+{keywordData.jobs.length - 3} más...</div>
              )}
            </div>
          </div>
        ))}
      </div>      {filteredKeywords.length === 0 && searchTerm && (
        <div className="no-results">
          <p>No se encontraron palabras clave que coincidan con "{searchTerm}"</p>
          <p>Intente buscar: Python, Java, Node, Apache, etc.</p>
        </div>
      )}

      {keywords.length === 0 && (
        <div className="no-data">
          <p>No se encontraron datos de análisis de vulnerabilidades en MongoDB.</p>
          <p>Ejecute algunos análisis de vulnerabilidades primero para ver reportes aquí.</p>
        </div>
      )}
    </div>
  );
};

export default GeneralReports;
