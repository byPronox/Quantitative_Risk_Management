import React, { useState, useEffect } from 'react';
import { reportService } from '../services/reports.js';

const ReportsPage = () => {
  const [reportTypes, setReportTypes] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generatedReports, setGeneratedReports] = useState([]);
  const [error, setError] = useState(null);

  // Form state
  const [selectedReportType, setSelectedReportType] = useState('vulnerability_summary');
  const [selectedFormat, setSelectedFormat] = useState('html');
  const [selectedSession, setSelectedSession] = useState('');
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeRecommendations, setIncludeRecommendations] = useState(true);

  useEffect(() => {
    loadReportTypes();
    loadSessions();
  }, []);

  const loadReportTypes = async () => {
    try {
      const data = await reportService.getReportTypes();
      setReportTypes(data);
    } catch (error) {
      console.error('Error loading report types:', error);
      setError('Failed to load report types');
    }
  };

  const loadSessions = async () => {
    try {
      // Fetch sessions from backend DocumentStore
      const response = await fetch('/api/v1/document-store/sessions');
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
      // Continue without sessions - user can still generate general reports
    }
  };

  const handleGenerateReport = async () => {
    setLoading(true);
    setError(null);

    try {
      const reportRequest = {
        report_type: selectedReportType,
        format: selectedFormat,
        session_id: selectedSession || null,
        include_charts: includeCharts,
        include_recommendations: includeRecommendations
      };

      const response = await reportService.generateReport(reportRequest);
      
      if (response.status === 'completed') {
        setGeneratedReports([...generatedReports, response]);
        
        // Auto-download PDF reports or open preview for HTML
        if (selectedFormat === 'pdf') {
          await reportService.downloadReport(response.report_id);
        } else if (selectedFormat === 'html') {
          window.open(reportService.getPreviewUrl(response.report_id), '_blank');
        }
      } else {
        setError('Report generation failed');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      setError('Failed to generate report: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (reportId) => {
    try {
      await reportService.downloadReport(reportId);
    } catch (error) {
      console.error('Error downloading report:', error);
      setError('Failed to download report');
    }
  };

  const handlePreviewReport = (reportId) => {
    window.open(reportService.getPreviewUrl(reportId), '_blank');
  };

  return (
    <div className="reports-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white shadow-xl rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h1 className="text-3xl font-bold text-gray-900">Generate Reports</h1>
            <p className="mt-2 text-gray-600">Create comprehensive vulnerability assessment reports</p>
          </div>

          <div className="p-6">
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <div className="mt-2 text-sm text-red-700">{error}</div>
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Report Generation Form */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Report Configuration</h2>
                
                {/* Report Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Report Type
                  </label>
                  <select
                    value={selectedReportType}
                    onChange={(e) => setSelectedReportType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="vulnerability_summary">Vulnerability Summary</option>
                    <option value="risk_assessment">Risk Assessment</option>
                    <option value="compliance_report">Compliance Report</option>
                    <option value="executive_summary">Executive Summary</option>
                  </select>
                </div>

                {/* Format */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Format
                  </label>
                  <div className="flex space-x-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="html"
                        checked={selectedFormat === 'html'}
                        onChange={(e) => setSelectedFormat(e.target.value)}
                        className="text-blue-600"
                      />
                      <span className="ml-2">HTML (Interactive)</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="pdf"
                        checked={selectedFormat === 'pdf'}
                        onChange={(e) => setSelectedFormat(e.target.value)}
                        className="text-blue-600"
                      />
                      <span className="ml-2">PDF (Printable)</span>
                    </label>
                  </div>
                </div>

                {/* Session Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Vulnerability Session (Optional)
                  </label>
                  <select
                    value={selectedSession}
                    onChange={(e) => setSelectedSession(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Sessions</option>
                    {sessions.map((session) => (
                      <option key={session.session_id} value={session.session_id}>
                        {session.session_id} - {new Date(session.created_at).toLocaleDateString()}
                        ({session.total_vulnerabilities} vulnerabilities)
                      </option>
                    ))}
                  </select>
                </div>

                {/* Options */}
                <div className="space-y-3">
                  <h3 className="text-lg font-medium text-gray-900">Report Options</h3>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={includeCharts}
                      onChange={(e) => setIncludeCharts(e.target.checked)}
                      className="text-blue-600"
                    />
                    <span className="ml-2">Include Charts and Visualizations</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={includeRecommendations}
                      onChange={(e) => setIncludeRecommendations(e.target.checked)}
                      className="text-blue-600"
                    />
                    <span className="ml-2">Include Recommendations</span>
                  </label>
                </div>

                {/* Generate Button */}
                <button
                  onClick={handleGenerateReport}
                  disabled={loading}
                  className={`w-full px-6 py-3 rounded-lg font-medium ${
                    loading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  } text-white transition-colors`}
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Generating Report...
                    </span>
                  ) : (
                    'Generate Report'
                  )}
                </button>
              </div>

              {/* Generated Reports List */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Generated Reports</h2>
                
                {generatedReports.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No reports generated yet.</p>
                    <p className="text-sm">Generate your first report to see it here.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {generatedReports.map((report) => (
                      <div key={report.report_id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-medium text-gray-900">
                              {report.report_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </h3>
                            <p className="text-sm text-gray-600">
                              Format: {report.format.toUpperCase()} • Generated: {new Date(report.created_at).toLocaleString()}
                            </p>
                            <p className="text-sm text-gray-600">
                              Status: <span className={`font-medium ${report.status === 'completed' ? 'text-green-600' : 'text-yellow-600'}`}>
                                {report.status}
                              </span>
                            </p>
                          </div>
                          <div className="flex space-x-2">
                            {report.format === 'html' && (
                              <button
                                onClick={() => handlePreviewReport(report.report_id)}
                                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm"
                              >
                                Preview
                              </button>
                            )}
                            <button
                              onClick={() => handleDownloadReport(report.report_id)}
                              className="px-3 py-1 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors text-sm"
                            >
                              Download
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
