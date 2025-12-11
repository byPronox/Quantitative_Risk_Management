import React, { useState, useEffect } from 'react';
import { backendApi } from '../services/api';
import '../styles/ScannerModule.css';

export default function ScannerModule() {
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
      const response = await backendApi.get('/scan/history');
      setScanHistory(response.data.scans || []);
    } catch (error) {
      console.error('Error loading scan history:', error);
    }
  };

  const startScan = async () => {
    if (!target.trim()) {
      setError('Por favor introduzca un objetivo para escanear');
      return;
    }

    setIsScanning(true);
    setError(null);
    setScanResults(null);

    try {
      const response = await backendApi.post('/scan/async', null, {
        params: { target: target.trim() }
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
      setError(error.response?.data?.detail || 'Escaneo falló');
      console.error('Scan error:', error);
    } finally {
      setIsScanning(false);
    }
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
    <div className="scanner-module">      <div className="scanner-header">
      <h2>🔍 Escáner de Red</h2>
      <p>Escanee redes y hosts en busca de vulnerabilidades usando Nmap</p>
    </div>

      {/* Scan Configuration */}
      <div className="scanner-config">
        <h3>⚙️ Configuración de Escaneo</h3>

        <div className="config-form">
          <div className="form-group">
            <label htmlFor="target">Objetivo (IP, Dominio, o Red):</label>
            <input
              type="text"
              id="target"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="ej: 192.168.1.1, example.com, 192.168.1.0/24"
              className="target-input"
            />
          </div>


          <button
            onClick={startScan}
            disabled={isScanning || !target.trim()}
            className={`scan-button ${isScanning ? 'scanning' : ''}`}
          >
            {isScanning ? (
              <>
                <div className="spinner" style={{ marginRight: '8px' }}></div>
                Escaneando... (puede tardar varios minutos)
              </>
            ) : (
              '🚀 Iniciar escaneo'
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
      {scanResults && (<div className="scan-results">
        <h3>📊 Resultados del Escaneo</h3>
        <div className="results-content">
          <div className="host-info">
            <h4>🎯 Objetivo: {scanResults.host || 'Desconocido'}</h4>
            <p><strong>Estado:</strong> {scanResults.status || 'Desconocido'}</p>
            <p><strong>SO:</strong> {scanResults.os || 'Desconocido'}</p>
          </div>

          {scanResults.ports && scanResults.ports.length > 0 && (
            <div className="ports-section">
              <h4>🔌 Puertos Abiertos ({scanResults.ports.length})</h4>
              <div className="ports-grid">
                {scanResults.ports.map((port, index) => (
                  <div key={index} className="port-item">
                    <span className="port-number">{port.port}</span>
                    <span className="port-state">{port.state}</span>
                    <span className="port-service">{port.service}</span>
                  </div>
                ))}
              </div>
            </div>
          )}            {scanResults.vulnerabilities && scanResults.vulnerabilities.length > 0 && (
            <div className="vulnerabilities-section">
              <h4>🚨 Vulnerabilidades Encontradas ({scanResults.vulnerabilities.length})</h4>
              <div className="vuln-list">
                {scanResults.vulnerabilities.map((vuln, index) => (
                  <div key={index} className="vuln-item">
                    <div className="vuln-header">
                      <span
                        className="severity-badge"
                        style={{ backgroundColor: getSeverityColor(vuln.severity) }}
                      >
                        {vuln.severity?.toUpperCase() || 'DESCONOCIDO'}
                      </span>                        <span className="vuln-title">{vuln.title || 'Vulnerabilidad Desconocida'}</span>
                    </div>
                    <p className="vuln-description">{vuln.description || 'Descripción no disponible'}</p>
                    {vuln.cve && (
                      <p className="vuln-cve">CVE: {vuln.cve}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}            {(!scanResults.vulnerabilities || scanResults.vulnerabilities.length === 0) && (
            <div className="no-vulnerabilities">
              <span className="check-icon">✅</span>
              <p>No se encontraron vulnerabilidades</p>
            </div>
          )}
        </div>
      </div>
      )}

      {/* Scan History */}
      {scanHistory.length > 0 && (<div className="scan-history">
        <h3>📋 Escaneos Recientes</h3>
        <div className="history-list">
          {scanHistory.slice(0, 5).map((scan) => (
            <div key={scan.id} className="history-item">
              <div className="history-header">
                <span className="scan-target">{scan.target}</span>
                <span className="scan-type">Escaneo de Vulnerabilidades</span>
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
