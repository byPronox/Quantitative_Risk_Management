import React, { useState } from 'react';
import './RiskAnalysisDashboard.css';

const RiskAnalysisDashboard = () => {
  const [target, setTarget] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState(null);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    if (!target.trim()) {
      setError('Por favor ingrese una IP o hostname válido');
      return;
    }

    setIsScanning(true);
    setError(null);
    setScanResults(null);

    try {
      const response = await fetch('/api/v1/risk/nmap-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ip: target,
          include_vulnerability_analysis: true,
          include_risk_rubric: true
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.error || 'Error en el escaneo');
      }

      const data = await response.json();
      setScanResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsScanning(false);
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return '#dc3545';
      case 'HIGH':
        return '#fd7e14';
      case 'MEDIUM':
        return '#ffc107';
      case 'LOW':
        return '#28a745';
      default:
        return '#6c757d';
    }
  };

  const getMitigationStrategyColor = (strategy) => {
    if (strategy?.includes('AVOID')) return '#dc3545';
    if (strategy?.includes('MITIGATE')) return '#fd7e14';
    if (strategy?.includes('TRANSFER')) return '#17a2b8';
    if (strategy?.includes('ACCEPT')) return '#28a745';
    return '#6c757d';
  };

  const getMitigationStrategyIcon = (strategy) => {
    if (strategy?.includes('AVOID')) return '🚫';
    if (strategy?.includes('MITIGATE')) return '🔧';
    if (strategy?.includes('TRANSFER')) return '🔄';
    if (strategy?.includes('ACCEPT')) return '✅';
    return '📋';
  };

  return (
    <div className="risk-analysis-dashboard">
      <div className="dashboard-header">
        <h1>🔍 Análisis de Riesgos con Rubrica AVOID/MITIGATE/TRANSFER/ACCEPT</h1>
        <p>Escaneo de vulnerabilidades con recomendaciones técnicas específicas</p>
      </div>

      <div className="scan-section">
        <div className="scan-input">
          <input
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Ingrese IP o hostname (ej: 192.168.1.1, example.com)"
            className="target-input"
            disabled={isScanning}
          />
          <button
            onClick={handleScan}
            disabled={isScanning || !target.trim()}
            className="scan-button"
          >
            {isScanning ? '🔍 Escaneando...' : '🚀 Iniciar Análisis'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}
      </div>

      {scanResults && (
        <div className="results-section">
          {/* Overall Risk Summary */}
          <div className="overall-risk-card">
            <h2>📊 Resumen General del Riesgo</h2>
            <div className="risk-summary">
              <div className="risk-level-badge" style={{ backgroundColor: getRiskLevelColor(scanResults.overall_risk_level) }}>
                {scanResults.overall_risk_level}
              </div>
              <div className="risk-details">
                <p><strong>Objetivo:</strong> {scanResults.target}</p>
                <p><strong>Timestamp:</strong> {new Date(scanResults.scan_timestamp).toLocaleString()}</p>
                <p><strong>Servicios Analizados:</strong> {scanResults.services_analysis.length}</p>
                <p><strong>Vulnerabilidades Encontradas:</strong> {scanResults.vulnerabilities_analysis.length}</p>
              </div>
            </div>
            <div className="technical-summary">
              <h3>📝 Resumen Técnico</h3>
              <p>{scanResults.technical_summary}</p>
            </div>
          </div>

          {/* Services Analysis */}
          {scanResults.services_analysis.length > 0 && (
            <div className="services-analysis">
              <h2>🖥️ Análisis de Servicios</h2>
              <div className="services-grid">
                {scanResults.services_analysis.map((service, index) => (
                  <div key={index} className="service-card">
                    <div className="service-header">
                      <h3>{service.service_name.toUpperCase()} - Puerto {service.port}</h3>
                      <div className="service-badges">
                        <span 
                          className="risk-badge" 
                          style={{ backgroundColor: getRiskLevelColor(service.risk_level) }}
                        >
                          {service.risk_level}
                        </span>
                        <span 
                          className="strategy-badge"
                          style={{ backgroundColor: getMitigationStrategyColor(service.mitigation_strategy) }}
                        >
                          {getMitigationStrategyIcon(service.mitigation_strategy)} {service.mitigation_strategy.split(' ')[0]}
                        </span>
                      </div>
                    </div>
                    
                    <div className="service-details">
                      <p><strong>Producto:</strong> {service.product || 'Desconocido'}</p>
                      <p><strong>Versión:</strong> {service.version || 'No detectada'}</p>
                      <p><strong>Protocolo:</strong> {service.protocol}</p>
                      <p><strong>Puntuación de Riesgo:</strong> {service.risk_score.toFixed(1)}/10</p>
                    </div>

                    <div className="mitigation-section">
                      <h4>🛡️ Estrategia de Mitigación</h4>
                      <p className="strategy-description">{service.mitigation_strategy}</p>
                      <p className="strategy-rationale">{service.strategy_rationale}</p>
                      
                      <div className="recommended-actions">
                        <h5>📋 Acciones Recomendadas:</h5>
                        <ul>
                          {service.recommended_actions.map((action, actionIndex) => (
                            <li key={actionIndex}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="technical-details">
                      <h5>🔬 Detalles Técnicos</h5>
                      <p>{service.technical_details}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Vulnerabilities Analysis */}
          {scanResults.vulnerabilities_analysis.length > 0 && (
            <div className="vulnerabilities-analysis">
              <h2>🚨 Análisis de Vulnerabilidades</h2>
              <div className="vulnerabilities-grid">
                {scanResults.vulnerabilities_analysis.map((vuln, index) => (
                  <div key={index} className="vulnerability-card">
                    <div className="vulnerability-header">
                      <h3>{vuln.vulnerability_id}</h3>
                      <div className="vulnerability-badges">
                        <span 
                          className="severity-badge" 
                          style={{ backgroundColor: getRiskLevelColor(vuln.severity) }}
                        >
                          {vuln.severity}
                        </span>
                        <span 
                          className="strategy-badge"
                          style={{ backgroundColor: getMitigationStrategyColor(vuln.mitigation_strategy) }}
                        >
                          {getMitigationStrategyIcon(vuln.mitigation_strategy)} {vuln.mitigation_strategy.split(' ')[0]}
                        </span>
                      </div>
                    </div>

                    <div className="vulnerability-output">
                      <h4>📄 Output del Escaneo</h4>
                      <pre className="output-text">{vuln.output}</pre>
                    </div>

                    <div className="mitigation-section">
                      <h4>🛡️ Estrategia de Mitigación</h4>
                      <p className="strategy-description">{vuln.mitigation_strategy}</p>
                      <p className="strategy-rationale">{vuln.strategy_rationale}</p>
                      
                      <div className="recommended-actions">
                        <h5>📋 Acciones Recomendadas:</h5>
                        <ul>
                          {vuln.recommended_actions.map((action, actionIndex) => (
                            <li key={actionIndex}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="technical-details">
                      <h5>🔬 Detalles Técnicos</h5>
                      <p>{vuln.technical_details}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Recommendations */}
          {scanResults.risk_recommendations.length > 0 && (
            <div className="risk-recommendations">
              <h2>💡 Recomendaciones de Riesgo</h2>
              <div className="recommendations-grid">
                {scanResults.risk_recommendations.map((rec, index) => (
                  <div key={index} className="recommendation-card">
                    <div className="recommendation-header">
                      <h3>{rec.title}</h3>
                      <span 
                        className="priority-badge"
                        style={{ 
                          backgroundColor: rec.priority === 'IMMEDIATE' ? '#dc3545' : 
                                          rec.priority === 'HIGH' ? '#fd7e14' : '#ffc107'
                        }}
                      >
                        {rec.priority}
                      </span>
                    </div>
                    <p className="recommendation-description">{rec.description}</p>
                    <div className="recommendation-actions">
                      <h4>Acciones Específicas:</h4>
                      <ul>
                        {rec.actions.map((action, actionIndex) => (
                          <li key={actionIndex}>{action}</li>
                        ))}
                      </ul>
                    </div>
                    <p className="recommendation-rationale">{rec.technical_rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mitigation Strategies Summary */}
          <div className="strategies-summary">
            <h2>📈 Resumen de Estrategias de Mitigación</h2>
            <div className="strategies-overview">
              <div className="strategies-applied">
                <h3>Estrategias Aplicadas:</h3>
                <div className="strategy-tags">
                  {scanResults.mitigation_strategies.strategies_applied.map((strategy, index) => (
                    <span key={index} className="strategy-tag">
                      {getMitigationStrategyIcon(strategy)} {strategy.split(' ')[0]}
                    </span>
                  ))}
                </div>
              </div>
              <div className="strategy-distribution">
                <h3>Distribución de Estrategias:</h3>
                {Object.entries(scanResults.mitigation_strategies.strategy_distribution).map(([strategy, count]) => (
                  <div key={strategy} className="strategy-count">
                    <span>{getMitigationStrategyIcon(strategy)} {strategy.split(' ')[0]}:</span>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskAnalysisDashboard;

