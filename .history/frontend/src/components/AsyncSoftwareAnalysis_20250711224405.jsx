import React, { useState, useEffect } from 'react';
import { 
  analyzeSoftwareAsync, 
  getQueueStatus, 
  pollAnalysisResults,
  startConsumer,
  stopConsumer,
  getConsumerStatus
} from '../services/nvd';
import { backendApi } from '../services/api';
import '../styles/AsyncSoftwareAnalysis.css';

export default function AsyncSoftwareAnalysis() {
  const [softwareList, setSoftwareList] = useState(['']);
  const [analysisParams, setAnalysisParams] = useState({
    includeCategories: ['high', 'critical'],
    maxResults: 50,
    includeHistorical: false
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState(null);
  const [queueStatus, setQueueStatus] = useState(null);
  const [consumerStatus, setConsumerStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [processedResults, setProcessedResults] = useState([]);
  const [jobsHistory, setJobsHistory] = useState([]); // Track all jobs sent to queue
  const [progress, setProgress] = useState(0);

  // Poll queue status and consumer status every 5 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [queueData, consumerData] = await Promise.all([
          getQueueStatus(),
          getConsumerStatus()
        ]);
        setQueueStatus(queueData);
        setConsumerStatus(consumerData);
        
        // If consumer is running, check for processed results
        if (consumerData.running && jobsHistory.length > 0) {
          await fetchProcessedResults();
        }
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobsHistory]);

  const addSoftwareInput = () => {
    setSoftwareList([...softwareList, '']);
  };

  const removeSoftwareInput = (index) => {
    const newList = softwareList.filter((_, i) => i !== index);
    setSoftwareList(newList.length > 0 ? newList : ['']);
  };

  const updateSoftware = (index, value) => {
    const newList = [...softwareList];
    newList[index] = value;
    setSoftwareList(newList);
  };

  const handleStartConsumer = async () => {
    try {
      const result = await startConsumer();
      console.log('Consumer started:', result);
      // Refresh status immediately
      const consumerData = await getConsumerStatus();
      setConsumerStatus(consumerData);
    } catch (error) {
      alert('Error al iniciar el consumidor: ' + error.message);
    }
  };

  const handleStopConsumer = async () => {
    try {
      const result = await stopConsumer();
      console.log('Consumer stopped:', result);
      // Refresh status immediately
      const consumerData = await getConsumerStatus();
      setConsumerStatus(consumerData);
    } catch (error) {
      alert('Error al detener el consumidor: ' + error.message);
    }
  };

  const startAnalysis = async () => {
    const validSoftware = softwareList.filter(software => software.trim() !== '');
    
    if (validSoftware.length === 0) {
      alert('Por favor, agrega al menos un software para analizar.');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setResults([]);

    try {
      // Send software list for async analysis
      const response = await analyzeSoftwareAsync(validSoftware, analysisParams);
      
      setAnalysisStatus({
        status: 'queued',
        jobIds: response.job_ids,
        estimatedTime: response.estimated_time,
        message: response.message
      });

      // Start polling for results
      pollAnalysisResults(response.job_ids, (update) => {
        if (update.error) {
          console.error('Polling error:', update.error);
          return;
        }

        setProgress(update.progress || 0);
        
        if (update.completed && update.completed.length > 0) {
          setResults(prev => {
            const newResults = [...prev];
            update.completed.forEach(result => {
              const existingIndex = newResults.findIndex(r => r.jobId === result.jobId);
              if (existingIndex >= 0) {
                newResults[existingIndex] = result;
              } else {
                newResults.push(result);
              }
            });
            return newResults;
          });
        }

        // Check if all jobs are complete
        if (update.progress >= 100) {
          setIsAnalyzing(false);
          setAnalysisStatus(prev => ({ ...prev, status: 'completed' }));
        }
      });

      // Track jobs history
      setJobsHistory(validSoftware.map((software, index) => ({
        jobId: response.job_ids[index],
        keyword: software
      })));

    } catch (error) {
      console.error('Error starting analysis:', error);
      setIsAnalyzing(false);
      alert('Error al iniciar el análisis: ' + error.message);
    }
  };

  // Function to fetch processed results from all jobs
  const fetchProcessedResults = async () => {
    if (jobsHistory.length === 0) return;
    
    const newProcessedResults = [];
    
    for (const job of jobsHistory) {
      try {
        // Check if this job has been processed
        const response = await fetch(`http://localhost:8000/nvd/results/${job.jobId}`);
        if (response.ok) {
          const result = await response.json();
          if (result.status === 'completed') {
            newProcessedResults.push({
              ...result,
              keyword: job.keyword,
              timestamp: new Date().toLocaleString()
            });
          }
        }
      } catch (error) {
        console.log(`Job ${job.jobId} not ready yet`);
      }
    }
    
    setProcessedResults(newProcessedResults);
  };

  return (
    <div className="async-software-analysis">
      <div className="analysis-header">
        <h2>🔍 Análisis Asíncrono de Software</h2>
        <p>Analiza múltiples software utilizando Kong Gateway + RabbitMQ para procesamiento asíncrono</p>
      </div>

      {/* Queue Status */}
      {queueStatus && (
        <div className="queue-status">
          <h4>📊 Estado de la Cola RabbitMQ</h4>
          <div className="status-grid">
            <div className="status-item">
              <span className="label">Pendientes:</span>
              <span className="value">{queueStatus.pending_jobs || 0}</span>
            </div>
            <div className="status-item">
              <span className="label">Procesando:</span>
              <span className="value">{queueStatus.processing_jobs || 0}</span>
            </div>
            <div className="status-item">
              <span className="label">Completados:</span>
              <span className="value">{queueStatus.completed_jobs || 0}</span>
            </div>
            <div className="status-item">
              <span className="label">Estado:</span>
              <span className={`value ${queueStatus.queue_health}`}>
                {queueStatus.queue_health}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Consumer Control */}
      {consumerStatus && (
        <div className="consumer-control">
          <h4>🤖 Control del Consumidor RabbitMQ</h4>
          <div className="consumer-status">
            <div className="status-info">
              <span className="label">Estado del Consumidor:</span>
              <span className={`value ${consumerStatus.running ? 'running' : 'stopped'}`}>
                {consumerStatus.running ? '🟢 Ejecutándose' : '🔴 Detenido'}
              </span>
            </div>
            <div className="consumer-actions">
              {!consumerStatus.running ? (
                <button onClick={handleStartConsumer} className="start-consumer-btn">
                  ▶️ Iniciar Consumidor
                </button>
              ) : (
                <button onClick={handleStopConsumer} className="stop-consumer-btn">
                  ⏹️ Detener Consumidor
                </button>
              )}
            </div>
            {consumerStatus.error && (
              <div className="consumer-error">
                ⚠️ {consumerStatus.error}
              </div>
            )}
          </div>
          <div className="consumer-info">
            <p>💡 <strong>Tip:</strong> El consumidor debe estar ejecutándose para procesar los trabajos de la cola automáticamente.</p>
          </div>
        </div>
      )}

      {/* Software Input */}
      <div className="software-input-section">
        <h3>📦 Lista de Software a Analizar</h3>
        {softwareList.map((software, index) => (
          <div key={index} className="software-input-row">
            <input
              type="text"
              value={software}
              onChange={(e) => updateSoftware(index, e.target.value)}
              placeholder={`Software ${index + 1} (ej: Apache, MySQL, Node.js)`}
              className="software-input"
            />
            {softwareList.length > 1 && (
              <button
                onClick={() => removeSoftwareInput(index)}
                className="remove-btn"
                type="button"
              >
                ❌
              </button>
            )}
          </div>
        ))}
        
        <button onClick={addSoftwareInput} className="add-software-btn" type="button">
          ➕ Agregar Software
        </button>
      </div>

      {/* Analysis Parameters */}
      <div className="analysis-params">
        <h3>⚙️ Parámetros de Análisis</h3>
        <div className="params-grid">
          <div className="param-group">
            <label>
              <input
                type="checkbox"
                checked={analysisParams.includeCategories.includes('critical')}
                onChange={(e) => {
                  const categories = e.target.checked 
                    ? [...analysisParams.includeCategories, 'critical']
                    : analysisParams.includeCategories.filter(c => c !== 'critical');
                  setAnalysisParams({...analysisParams, includeCategories: categories});
                }}
              />
              Vulnerabilidades Críticas
            </label>
          </div>
          <div className="param-group">
            <label>
              <input
                type="checkbox"
                checked={analysisParams.includeCategories.includes('high')}
                onChange={(e) => {
                  const categories = e.target.checked 
                    ? [...analysisParams.includeCategories, 'high']
                    : analysisParams.includeCategories.filter(c => c !== 'high');
                  setAnalysisParams({...analysisParams, includeCategories: categories});
                }}
              />
              Vulnerabilidades Altas
            </label>
          </div>
          <div className="param-group">
            <label>
              Máximo de resultados:
              <input
                type="number"
                value={analysisParams.maxResults}
                onChange={(e) => setAnalysisParams({
                  ...analysisParams, 
                  maxResults: parseInt(e.target.value) || 50
                })}
                min="10"
                max="200"
              />
            </label>
          </div>
        </div>
      </div>

      {/* Start Analysis Button */}
      <div className="analysis-action">
        <button 
          onClick={startAnalysis} 
          disabled={isAnalyzing}
          className={`analyze-btn ${isAnalyzing ? 'analyzing' : ''}`}
        >
          {isAnalyzing ? (
            <>
              <div className="spinner"></div>
              Analizando... ({Math.round(progress)}%)
            </>
          ) : (
            <>🚀 Iniciar Análisis Asíncrono</>
          )}
        </button>
      </div>

      {/* Analysis Status */}
      {analysisStatus && (
        <div className="analysis-status">
          <h4>📈 Estado del Análisis</h4>
          <div className="status-info">
            <p><strong>Estado:</strong> {analysisStatus.status}</p>
            <p><strong>Jobs ID:</strong> {analysisStatus.jobIds?.join(', ')}</p>
            <p><strong>Tiempo estimado:</strong> {analysisStatus.estimatedTime} segundos</p>
            {progress > 0 && (
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                ></div>
                <span className="progress-text">{Math.round(progress)}%</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="analysis-results">
          <h4>📊 Resultados del Análisis</h4>
          {results.map((result, index) => (
            <div key={result.jobId} className="result-item">
              <h5>Job #{index + 1} - {result.jobId}</h5>
              <div className="result-content">
                {result.status === 'completed' ? (
                  <div className="vulnerabilities">
                    {result.vulnerabilities?.length > 0 ? (
                      <>
                        <p><strong>Vulnerabilidades encontradas:</strong> {result.vulnerabilities.length}</p>
                        <div className="vuln-list">
                          {result.vulnerabilities.slice(0, 3).map((vuln, vIndex) => (
                            <div key={vIndex} className="vuln-item">
                              <strong>{vuln.id}</strong>: {vuln.description}
                              {vuln.severity && (
                                <span className={`severity ${vuln.severity.toLowerCase()}`}>
                                  {vuln.severity}
                                </span>
                              )}
                            </div>
                          ))}
                          {result.vulnerabilities.length > 3 && (
                            <p>... y {result.vulnerabilities.length - 3} más</p>
                          )}
                        </div>
                      </>
                    ) : (
                      <p>✅ No se encontraron vulnerabilidades</p>
                    )}
                  </div>
                ) : result.status === 'failed' ? (
                  <p className="error">❌ Error: {result.error}</p>
                ) : (
                  <p>⏳ Procesando...</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Processed Results from Consumer */}
      {processedResults.length > 0 && (
        <div className="processed-results">
          <h4>✨ Resultados Procesados por el Consumidor</h4>
          <p className="processed-info">🤖 Estos resultados fueron procesados automáticamente por el consumidor RabbitMQ usando Kong Gateway:</p>
          
          {processedResults.map((result, index) => (
            <div key={`processed-${index}`} className="processed-result-item">
              <div className="result-header">
                <h5>🔍 {result.keyword}</h5>
                <span className="result-timestamp">⏰ {result.timestamp}</span>
              </div>
              
              <div className="result-summary">
                <div className="summary-stats">
                  <span className="stat-item">
                    📊 <strong>{result.total_results || 0}</strong> vulnerabilidades encontradas
                  </span>
                  <span className="stat-item">
                    🌐 Procesado via <strong>{result.processed_via || 'Kong Gateway'}</strong>
                  </span>
                </div>
              </div>
              
              {result.vulnerabilities && result.vulnerabilities.length > 0 && (
                <div className="vulnerabilities-showcase">
                  <h6>🚨 Top Vulnerabilidades:</h6>
                  <div className="vuln-grid">
                    {result.vulnerabilities.slice(0, 6).map((vuln, vIndex) => {
                      const cve = vuln.cve || {};
                      const metrics = cve.metrics || {};
                      
                      // Extract impact information
                      let impactInfo = { score: 0, severity: 'UNKNOWN', impacts: {} };
                      
                      if (metrics.cvssMetricV31 && metrics.cvssMetricV31.length > 0) {
                        const cvss = metrics.cvssMetricV31[0].cvssData;
                        impactInfo = {
                          score: cvss.baseScore || 0,
                          severity: cvss.baseSeverity || 'UNKNOWN',
                          impacts: {
                            confidentiality: cvss.confidentialityImpact || 'NONE',
                            integrity: cvss.integrityImpact || 'NONE',
                            availability: cvss.availabilityImpact || 'NONE'
                          },
                          impactScore: metrics.cvssMetricV31[0].impactScore || 0
                        };
                      } else if (metrics.cvssMetricV30 && metrics.cvssMetricV30.length > 0) {
                        const cvss = metrics.cvssMetricV30[0].cvssData;
                        impactInfo = {
                          score: cvss.baseScore || 0,
                          severity: cvss.baseSeverity || 'UNKNOWN',
                          impacts: {
                            confidentiality: cvss.confidentialityImpact || 'NONE',
                            integrity: cvss.integrityImpact || 'NONE',
                            availability: cvss.availabilityImpact || 'NONE'
                          },
                          impactScore: metrics.cvssMetricV30[0].impactScore || 0
                        };
                      }
                      
                      return (
                        <div key={vIndex} className="vuln-card">
                          <div className="vuln-header">
                            <strong className="cve-id">{cve.id}</strong>
                            <span className={`severity-badge ${impactInfo.severity.toLowerCase()}`}>
                              {impactInfo.severity}
                            </span>
                          </div>
                          
                          <div className="vuln-description">
                            {cve.descriptions && cve.descriptions[0] ? 
                              cve.descriptions[0].value.substring(0, 100) + '...' : 
                              'Sin descripción disponible'
                            }
                          </div>
                          
                          <div className="impact-details">
                            <div className="score-info">
                              <span className="base-score">⚡ Score: <strong>{impactInfo.score}</strong></span>
                              <span className="impact-score">💥 Impact: <strong>{impactInfo.impactScore}</strong></span>
                            </div>
                            <div className="impact-types">
                              <span className={`impact-item ${impactInfo.impacts.confidentiality.toLowerCase()}`}>
                                🔒 C: {impactInfo.impacts.confidentiality}
                              </span>
                              <span className={`impact-item ${impactInfo.impacts.integrity.toLowerCase()}`}>
                                ✅ I: {impactInfo.impacts.integrity}
                              </span>
                              <span className={`impact-item ${impactInfo.impacts.availability.toLowerCase()}`}>
                                🔄 A: {impactInfo.impacts.availability}
                              </span>
                            </div>
                          </div>
                          
                          <div className="vuln-dates">
                            <small>📅 Publicado: {cve.published ? new Date(cve.published).toLocaleDateString() : 'N/A'}</small>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {result.vulnerabilities.length > 6 && (
                    <div className="more-results">
                      <p>... y <strong>{result.vulnerabilities.length - 6}</strong> vulnerabilidades más</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
