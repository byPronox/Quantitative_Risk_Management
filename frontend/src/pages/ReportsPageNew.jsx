import React, { useState } from 'react';
import GeneralReports from '../components/GeneralReports';
import { reportService } from '../services/reports.js';

const ReportsPage = () => {
  const [activeTab, setActiveTab] = useState('general');
  const [loading, setLoading] = useState(false);
  const [generatedReports, setGeneratedReports] = useState([]);
  const [error, setError] = useState(null);

  // Form state for PDF/HTML reports
  const [selectedReportType, setSelectedReportType] = useState('vulnerability_summary');
  const [selectedFormat, setSelectedFormat] = useState('html');
  const [selectedSession, setSelectedSession] = useState('');
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeRecommendations, setIncludeRecommendations] = useState(true);

  const handleGenerateReport = async () => {
    setLoading(true);
    setError(null);

    try {
      const reportRequest = {
        report_type: selectedReportType,
        format: selectedFormat,
        session_id: selectedSession || null,
        options: {
          include_charts: includeCharts,
          include_recommendations: includeRecommendations
        }
      };

      const result = await reportService.generateReport(reportRequest);
      
      if (result.success) {
        setGeneratedReports(prev => [result, ...prev]);
        
        // If it's a downloadable format, trigger download
        if (result.download_url) {
          const link = document.createElement('a');
          link.href = result.download_url;
          link.download = result.filename || 'report';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      } else {
        setError(result.error || 'Failed to generate report');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      setError('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', color: '#2c3e50', marginBottom: '30px' }}>
        Reports Dashboard
      </h1>

      {/* Tab Navigation */}
      <div style={{ marginBottom: '30px', borderBottom: '2px solid #e9ecef' }}>
        <div style={{ display: 'flex', gap: '0' }}>
          <button
            onClick={() => setActiveTab('general')}
            style={{
              padding: '15px 30px',
              border: 'none',
              background: activeTab === 'general' ? '#007bff' : '#f8f9fa',
              color: activeTab === 'general' ? 'white' : '#6c757d',
              borderRadius: '8px 8px 0 0',
              cursor: 'pointer',
              fontSize: '1.1rem',
              fontWeight: activeTab === 'general' ? 'bold' : 'normal',
              transition: 'all 0.3s ease'
            }}
          >
            General Reports
          </button>
          <button
            onClick={() => setActiveTab('custom')}
            style={{
              padding: '15px 30px',
              border: 'none',
              background: activeTab === 'custom' ? '#007bff' : '#f8f9fa',
              color: activeTab === 'custom' ? 'white' : '#6c757d',
              borderRadius: '8px 8px 0 0',
              cursor: 'pointer',
              fontSize: '1.1rem',
              fontWeight: activeTab === 'custom' ? 'bold' : 'normal',
              transition: 'all 0.3s ease'
            }}
          >
            Custom Reports
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'general' ? (
        <GeneralReports />
      ) : (
        <div style={{ 
          background: 'white', 
          padding: '30px', 
          borderRadius: '12px', 
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' 
        }}>
          <h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>Custom PDF/HTML Reports</h2>
          
          {error && (
            <div style={{
              background: '#f8d7da',
              color: '#721c24',
              padding: '15px',
              borderRadius: '6px',
              marginBottom: '20px',
              border: '1px solid #f5c6cb'
            }}>
              {error}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '30px' }}>
            
            {/* Report Type Selection */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#495057' }}>
                Report Type:
              </label>
              <select
                value={selectedReportType}
                onChange={(e) => setSelectedReportType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ced4da',
                  borderRadius: '6px',
                  fontSize: '1rem'
                }}
              >
                <option value="vulnerability_summary">Vulnerability Summary</option>
                <option value="detailed_analysis">Detailed Analysis</option>
                <option value="trend_analysis">Trend Analysis</option>
                <option value="compliance_report">Compliance Report</option>
              </select>
            </div>

            {/* Format Selection */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#495057' }}>
                Format:
              </label>
              <select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ced4da',
                  borderRadius: '6px',
                  fontSize: '1rem'
                }}
              >
                <option value="html">HTML</option>
                <option value="pdf">PDF</option>
              </select>
            </div>

            {/* Session Selection */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#495057' }}>
                Session (Optional):
              </label>
              <input
                type="text"
                value={selectedSession}
                onChange={(e) => setSelectedSession(e.target.value)}
                placeholder="Enter session ID or leave empty for all data"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ced4da',
                  borderRadius: '6px',
                  fontSize: '1rem'
                }}
              />
            </div>
          </div>

          {/* Options */}
          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ color: '#495057', marginBottom: '15px' }}>Report Options</h3>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeCharts}
                  onChange={(e) => setIncludeCharts(e.target.checked)}
                  style={{ transform: 'scale(1.2)' }}
                />
                <span>Include Charts</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeRecommendations}
                  onChange={(e) => setIncludeRecommendations(e.target.checked)}
                  style={{ transform: 'scale(1.2)' }}
                />
                <span>Include Recommendations</span>
              </label>
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerateReport}
            disabled={loading}
            style={{
              background: loading ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none',
              padding: '15px 30px',
              borderRadius: '6px',
              fontSize: '1.1rem',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.3s ease'
            }}
          >
            {loading ? 'Generating Report...' : 'Generate Report'}
          </button>

          {/* Generated Reports List */}
          {generatedReports.length > 0 && (
            <div style={{ marginTop: '40px' }}>
              <h3 style={{ color: '#2c3e50', marginBottom: '20px' }}>Generated Reports</h3>
              <div style={{ display: 'grid', gap: '15px' }}>
                {generatedReports.map((report, index) => (
                  <div key={index} style={{
                    background: '#f8f9fa',
                    padding: '15px',
                    borderRadius: '8px',
                    border: '1px solid #dee2e6',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <strong>{report.filename || 'Report'}</strong>
                      <br />
                      <small style={{ color: '#6c757d' }}>
                        {report.created_at ? new Date(report.created_at).toLocaleString() : 'Just now'}
                      </small>
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      {report.download_url && (
                        <a
                          href={report.download_url}
                          download
                          style={{
                            background: '#007bff',
                            color: 'white',
                            padding: '8px 16px',
                            borderRadius: '4px',
                            textDecoration: 'none',
                            fontSize: '0.9rem'
                          }}
                        >
                          Download
                        </a>
                      )}
                      {report.preview_url && (
                        <a
                          href={report.preview_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            background: '#28a745',
                            color: 'white',
                            padding: '8px 16px',
                            borderRadius: '4px',
                            textDecoration: 'none',
                            fontSize: '0.9rem'
                          }}
                        >
                          Preview
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReportsPage;
