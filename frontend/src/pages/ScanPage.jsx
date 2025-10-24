import React, { useState, useEffect } from 'react';
import { backendApi } from '../services/api';
import '../styles/ScanPage.css';

export default function ScanPage() {
  const [target, setTarget] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadScanHistory();
  }, []);

  const loadScanHistory = async () => {
    try {
      const response = await backendApi.get('/nmap/history');
      setScanHistory(response.data.scans || []);
    } catch (error) {
      console.error('Error loading scan history:', error);
    }
  };

  const startScan = async () => {
    if (!target.trim()) {
      setError('Please enter a target to scan');
      return;
    }

    setIsScanning(true);
    setError(null);
    setScanResults(null);

    try {
      const response = await backendApi.post('/nmap/scan', {
        ip: target.trim()
      });

      setScanResults(response.data);
      
      // Add to history
      const newScan = {
        id: Date.now(),
        target: target.trim(),
        status: 'completed',
        timestamp: new Date().toISOString(),
        results: response.data
      };
      
      setScanHistory(prev => [newScan, ...prev]);
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Scan failed');
      console.error('Scan error:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const formatScanResults = (results) => {
    if (!results) return null;
    
    return {
      host: results.host || 'Unknown',
      status: results.status || 'Unknown',
      ports: results.ports || [],
      services: results.services || [],
      vulnerabilities: results.vulnerabilities || [],
      os: results.os || 'Unknown'
    };
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  return (
    <div className="scan-page">
      <div className="scan-header">
        <h1>🔍 Network Scanner</h1>
        <p>Scan networks and hosts for vulnerabilities using Nmap</p>
      </div>

      {/* Scan Configuration */}
      <div className="scan-config">
        <h3>⚙️ Scan Configuration</h3>
        
        <div className="config-form">
          <div className="form-group">
            <label htmlFor="target">Target (IP, Domain, or Network):</label>
            <input
              type="text"
              id="target"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="e.g., 192.168.1.1, example.com, 192.168.1.0/24"
              className="target-input"
            />
          </div>
          {/* Scan Type eliminado: solo escaneo completo */}
          <button
            onClick={startScan}
            disabled={isScanning || !target.trim()}
            className={`scan-button ${isScanning ? 'scanning' : ''}`}
          >
            {isScanning ? (
              <>
                <div className="spinner"></div>
                Scanning...
              </>
            ) : (
              '🚀 Start Scan'
            )}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Current Scan Results */}
      {scanResults && (
        <div className="scan-results">
          <h3>📊 Scan Results</h3>
          <div className="results-content">
            {(() => {
              const formatted = formatScanResults(scanResults);
              return (
                <>
                  <div className="host-info">
                    <h4>🎯 Target: {formatted.host}</h4>
                    <p><strong>Status:</strong> {formatted.status}</p>
                    <p><strong>OS:</strong> {formatted.os}</p>
                  </div>

                  {formatted.ports.length > 0 && (
                    <div className="ports-section">
                      <h4>🔌 Open Ports ({formatted.ports.length})</h4>
                      <div className="ports-grid">
                        {formatted.ports.map((port, index) => (
                          <div key={index} className="port-item">
                            <span className="port-number">{port.port}</span>
                            <span className="port-state">{port.state}</span>
                            <span className="port-service">{port.service}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {formatted.vulnerabilities.length > 0 && (
                    <div className="vulnerabilities-section">
                      <h4>🚨 Vulnerabilities Found ({formatted.vulnerabilities.length})</h4>
                      <div className="vuln-list">
                        {formatted.vulnerabilities.map((vuln, index) => (
                          <div key={index} className="vuln-item">
                            <div className="vuln-header">
                              <span 
                                className="severity-badge"
                                style={{ backgroundColor: getSeverityColor(vuln.severity) }}
                              >
                                {vuln.severity?.toUpperCase() || 'UNKNOWN'}
                              </span>
                              <span className="vuln-title">{vuln.title || 'Unknown Vulnerability'}</span>
                            </div>
                            <p className="vuln-description">{vuln.description || 'No description available'}</p>
                            {vuln.cve && (
                              <p className="vuln-cve">CVE: {vuln.cve}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {formatted.vulnerabilities.length === 0 && (
                    <div className="no-vulnerabilities">
                      <span className="check-icon">✅</span>
                      <p>No vulnerabilities found</p>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        </div>
      )}

      {/* Scan History */}
      {scanHistory.length > 0 && (
        <div className="scan-history">
          <h3>📋 Scan History</h3>
          <div className="history-list">
            {scanHistory.map((scan) => (
              <div key={scan.id} className="history-item">
                <div className="history-header">
                  <span className="scan-target">{scan.target}</span>
                  <span className="scan-type">Vulnerability Scan</span>
                  <span className="scan-time">
                    {new Date(scan.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="history-status">
                  <span className={`status-badge ${scan.status}`}>
                    {scan.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
