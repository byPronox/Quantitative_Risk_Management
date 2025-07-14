import React, { useState, useEffect } from 'react';
import './GeneralReports.css';

const GeneralReports = () => {
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  const [detailedReport, setDetailedReport] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Fetch keywords summary on component mount
  useEffect(() => {
    fetchKeywordsSummary();
  }, []);

  const fetchKeywordsSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/reports/general/keywords');
      const data = await response.json();
      
      if (data.success) {
        setKeywords(data.keywords);
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

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  if (loading) {
    return (
      <div className="general-reports">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading General Reports...</p>
        </div>
      </div>
    );
  }

  if (selectedKeyword && detailedReport) {
    return (
      <div className="general-reports">
        <div className="report-header">
          <button className="back-button" onClick={goBackToSummary}>
            ← Back to Summary
          </button>
          <h2>Detailed Report: {selectedKeyword}</h2>
        </div>

        {loadingDetails ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading detailed report...</p>
          </div>
        ) : (
          <div className="detailed-report">
            {/* Summary Cards */}
            <div className="summary-cards">
              <div className="summary-card">
                <h3>Total Analyses</h3>
                <p className="metric">{detailedReport.total_jobs}</p>
              </div>
              <div className="summary-card">
                <h3>Total Vulnerabilities</h3>
                <p className="metric">{detailedReport.total_vulnerabilities}</p>
              </div>
              <div className="summary-card">
                <h3>Software</h3>
                <p className="metric">{selectedKeyword}</p>
              </div>
            </div>

            {/* Severity Distribution */}
            <div className="section">
              <h3>Severity Distribution</h3>
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
            </div>

            {/* Vulnerabilities by Year */}
            <div className="section">
              <h3>Vulnerabilities by Year</h3>
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
            </div>

            {/* Recent Vulnerabilities */}
            <div className="section">
              <h3>Recent Vulnerabilities (Top 10)</h3>
              <div className="vulnerabilities-table">
                <table>
                  <thead>
                    <tr>
                      <th>CVE ID</th>
                      <th>Severity</th>
                      <th>Score</th>
                      <th>Published</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailedReport.vulnerabilities.slice(0, 10).map((vuln, index) => {
                      const cve = vuln.cve || {};
                      const metrics = cve.metrics || {};
                      let severity = 'Unknown';
                      let score = 'N/A';
                      
                      if (metrics.cvssMetricV31 && metrics.cvssMetricV31.length > 0) {
                        severity = metrics.cvssMetricV31[0].cvssData?.baseSeverity || 'Unknown';
                        score = metrics.cvssMetricV31[0].cvssData?.baseScore || 'N/A';
                      } else if (metrics.cvssMetricV2 && metrics.cvssMetricV2.length > 0) {
                        score = metrics.cvssMetricV2[0].cvssData?.baseScore || 'N/A';
                        if (score >= 9.0) severity = 'Critical';
                        else if (score >= 7.0) severity = 'High';
                        else if (score >= 4.0) severity = 'Medium';
                        else severity = 'Low';
                      }

                      const description = cve.descriptions?.find(d => d.lang === 'en')?.value || 'No description available';
                      
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
            </div>

            {/* Analysis History */}
            <div className="section">
              <h3>Analysis History</h3>
              <div className="jobs-history">
                {detailedReport.jobs.map((job, index) => (
                  <div key={index} className="job-item">
                    <div className="job-header">
                      <span className="job-id">Job: {job.job_id}</span>
                      <span className="job-date">{job.processed_at_readable}</span>
                    </div>
                    <div className="job-stats">
                      <span>Results: {job.total_results}</span>
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
    <div className="general-reports">
      <div className="header">
        <h2>General Reports</h2>
        <p>Click on any software keyword to view detailed vulnerability analysis</p>
      </div>

      <div className="keywords-grid">
        {keywords.map((keywordData, index) => (
          <div 
            key={index} 
            className="keyword-card"
            onClick={() => fetchDetailedReport(keywordData.keyword)}
          >
            <div className="keyword-header">
              <h3>{keywordData.keyword}</h3>
              <span className="vulnerability-count">{keywordData.total_vulnerabilities} vulnerabilities</span>
            </div>
            <div className="keyword-stats">
              <div className="stat">
                <span className="label">Total Analyses:</span>
                <span className="value">{keywordData.total_jobs}</span>
              </div>
              <div className="stat">
                <span className="label">Latest Analysis:</span>
                <span className="value">{keywordData.latest_analysis}</span>
              </div>
            </div>
            <div className="jobs-preview">
              <h4>Recent Jobs:</h4>
              {keywordData.jobs.slice(0, 3).map((job, jobIndex) => (
                <div key={jobIndex} className="job-preview">
                  <span className="job-id">{job.job_id}</span>
                  <span className="job-vulns">{job.vulnerabilities_count} vulns</span>
                </div>
              ))}
              {keywordData.jobs.length > 3 && (
                <div className="more-jobs">+{keywordData.jobs.length - 3} more...</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {keywords.length === 0 && (
        <div className="no-data">
          <p>No vulnerability analysis data found in MongoDB.</p>
          <p>Run some vulnerability analyses first to see reports here.</p>
        </div>
      )}
    </div>
  );
};

export default GeneralReports;
