import React, { useState, useEffect } from 'react';
import { 
  analyzeSoftwareAsync, 
  getQueueStatus, 
  pollAnalysisResults,
  startConsumer,
  stopConsumer,
  getConsumerStatus,
  getAllQueueResults
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
  const [newResultsCount, setNewResultsCount] = useState(0);
  const [allQueueResults, setAllQueueResults] = useState([]); // All completed jobs from queue

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
        
        // If consumer is running, check for processed results and load all results
        if (consumerData.running) {
          if (jobsHistory.length > 0) {
            await fetchProcessedResults();
          }
          // Also refresh all queue results
          await loadAllQueueResults();
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

  // Function to load all queue results
  const loadAllQueueResults = async () => {
    try {
      const allResults = await getAllQueueResults();
      if (allResults.success) {
        setAllQueueResults(allResults.jobs);
      }
    } catch (error) {
      console.error('Error loading all queue results:', error);
    }
  };

  const handleStartConsumer = async () => {
    try {
      const result = await startConsumer();
      console.log('Consumer started:', result);
      // Refresh status immediately
      const consumerData = await getConsumerStatus();
      setConsumerStatus(consumerData);
      // Load all queue results when consumer starts
      await loadAllQueueResults();
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
    
    let newResultsFound = 0;
    
    for (const job of jobsHistory) {
      try {
        // Check if this job has been processed
        const response = await backendApi.get(`/nvd/results/${job.jobId}`);
        if (response.status === 200 && response.data.status === 'completed') {
          // Check if we already have this result
          const existingResultIndex = processedResults.findIndex(r => r.keyword === job.keyword);
          
          const newResult = {
            ...response.data,
            keyword: job.keyword,
            timestamp: new Date().toLocaleString()
          };
          
          setProcessedResults(prevResults => {
            const updated = [...prevResults];
            if (existingResultIndex >= 0) {
              updated[existingResultIndex] = newResult; // Update existing
            } else {
              updated.push(newResult); // Add new
              newResultsFound++;
            }
            return updated;
          });
        }
      } catch (error) {
        console.log(`Job ${job.jobId} not ready yet:`, error.message);
      }
    }
    
    // Update new results counter
    if (newResultsFound > 0) {
      setNewResultsCount(prev => prev + newResultsFound);
      // Reset counter after 10 seconds
      setTimeout(() => setNewResultsCount(0), 10000);
    }
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
          <div className="processed-header">
            <h4>✨ Resultados Procesados por el Consumidor</h4>
            {newResultsCount > 0 && (
              <div className="new-results-notification">
                🎉 ¡{newResultsCount} nuevo{newResultsCount > 1 ? 's' : ''} resultado{newResultsCount > 1 ? 's' : ''} procesado{newResultsCount > 1 ? 's' : ''}!
              </div>
            )}
          </div>
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

      {/* All Queue Results */}
      {consumerStatus && consumerStatus.running && allQueueResults.length > 0 && (
        <div className="all-queue-results">
          <div className="results-header">
            <h4>📋 Todos los Resultados de la Cola</h4>
            <div className="results-summary">
              <span className="summary-item">
                🎯 Total de trabajos completados: <strong>{allQueueResults.length}</strong>
              </span>
              <button onClick={loadAllQueueResults} className="refresh-results-btn">
                🔄 Actualizar
              </button>
            </div>
          </div>
          
          <div className="queue-results-grid">
            {allQueueResults.map((job, index) => {
              const totalVulnerabilities = job.total_results || 0;
              const vulnerabilities = job.vulnerabilities || [];
              
              // Calculate severity counts
              const severityCounts = vulnerabilities.reduce((counts, vuln) => {
                const severity = vuln.cve?.metrics?.cvssMetricV2?.[0]?.baseSeverity || 'UNKNOWN';
                counts[severity] = (counts[severity] || 0) + 1;
                return counts;
              }, {});

              return (
                <div key={`queue-${job.job_id}`} className="queue-result-card">
                  <div className="card-header">
                    <div className="job-info">
                      <h5 className="keyword-title">🔍 {job.keyword}</h5>
                      <div className="job-meta">
                        <span className="job-id">ID: {job.job_id.substring(0, 8)}...</span>
                        <span className="processed-time">
                          ⏰ {job.processed_at ? new Date(job.processed_at * 1000).toLocaleString() : 'Recientemente'}
                        </span>
                      </div>
                    </div>
                    <div className="results-count">
                      <span className="total-count">{totalVulnerabilities} vulnerabilidades</span>
                    </div>
                  </div>

                  <div className="severity-summary">
                    <div className="severity-stats">
                      {severityCounts.HIGH > 0 && (
                        <span className="severity-badge high">
                          🔴 Alta: {severityCounts.HIGH}
                        </span>
                      )}
                      {severityCounts.MEDIUM > 0 && (
                        <span className="severity-badge medium">
                          🟡 Media: {severityCounts.MEDIUM}
                        </span>
                      )}
                      {severityCounts.LOW > 0 && (
                        <span className="severity-badge low">
                          🟢 Baja: {severityCounts.LOW}
                        </span>
                      )}
                      {Object.keys(severityCounts).length === 0 && (
                        <span className="no-vulnerabilities">✅ Sin vulnerabilidades</span>
                      )}
                    </div>
                  </div>

                  {vulnerabilities.length > 0 && (
                    <div className="vulnerabilities-preview">
                      <h6>🔸 Vista previa de vulnerabilidades:</h6>
                      <div className="vuln-preview-list">
                        {vulnerabilities.slice(0, 3).map((vuln, vIndex) => {
                          const cve = vuln.cve || {};
                          const severity = cve.metrics?.cvssMetricV2?.[0]?.baseSeverity || 'UNKNOWN';
                          const score = cve.metrics?.cvssMetricV2?.[0]?.cvssData?.baseScore || 'N/A';
                          const description = cve.descriptions?.[0]?.value || 'Sin descripción';

                          return (
                            <div key={vIndex} className="vuln-preview-item">
                              <div className="vuln-preview-header">
                                <strong className="cve-id-small">{cve.id}</strong>
                                <span className={`severity-badge-small ${severity.toLowerCase()}`}>
                                  {severity} ({score})
                                </span>
                              </div>
                              <div className="vuln-preview-desc">
                                {description.length > 80 ? 
                                  description.substring(0, 80) + '...' : 
                                  description
                                }
                              </div>
                            </div>
                          );
                        })}
                        {vulnerabilities.length > 3 && (
                          <div className="more-vulns-indicator">
                            <span>... y {vulnerabilities.length - 3} vulnerabilidades más</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="card-footer">
                    <div className="processed-info">
                      <span className="processed-via">
                        🚀 Procesado vía: {job.processed_via || 'queue_consumer'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
