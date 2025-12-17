import React, { useState, useEffect } from 'react';
import {
  analyzeSoftwareAsync,
  getQueueStatus,
  pollAnalysisResults,
  startConsumer,
  stopConsumer,
  getConsumerStatus,
  getAllQueueResults,
  getNvdHistory
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
  const [dbHistory, setDbHistory] = useState([]); // History from Supabase
  const [consumerButtonLoading, setConsumerButtonLoading] = useState(false);

  // Function to load history from Supabase
  const loadDbHistory = async () => {
    try {
      const history = await getNvdHistory();
      setDbHistory(history || []);
    } catch (error) {
      console.error('Error loading DB history:', error);
    }
  };

  // Function to load all jobs (pending, processing, completed)
  const loadAllQueueJobs = async () => {
    try {
      const response = await backendApi.get('/nvd/queue/jobs');
      if (response.data && response.data.jobs) {
        setAllQueueResults(response.data.jobs);
      }
    } catch (error) {
      console.error('Error loading all queue jobs:', error);
    }
  };

  // Poll queue status and consumer status every 5 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [queueData, consumerData] = await Promise.all([
          getQueueStatus(),
          getConsumerStatus()
        ]);

        // Update queue status with dynamic completed count if consumer is running
        if (consumerData.running && allQueueResults.length > 0) {
          queueData.completed_jobs = allQueueResults.length;
          queueData.pending_jobs = Math.max(0, (queueData.pending_jobs || 0));
        }

        setQueueStatus(queueData);
        setConsumerStatus(consumerData);

        // Always check for processed results and load all results
        if (jobsHistory.length > 0) {
          await fetchProcessedResults();
        }
        // Also refresh all queue results
        await loadAllQueueResults();
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobsHistory, allQueueResults]);

  // Load all queue results on component mount
  useEffect(() => {
    loadAllQueueResults();
    loadAllQueueJobs();
    loadDbHistory();
  }, []);

  // Update queue completed count when allQueueResults changes
  useEffect(() => {
    if (allQueueResults.length > 0 && consumerStatus?.running) {
      setQueueStatus(prevStatus => ({
        ...prevStatus,
        completed_jobs: allQueueResults.length,
        pending_jobs: Math.max(0, (prevStatus?.pending_jobs || 0) - allQueueResults.length),
        queue_health: 'healthy'
      }));
    }
  }, [allQueueResults, consumerStatus]);

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
      // This is the fix: check for a successful response and extract the 'jobs' array
      if (allResults && allResults.success) {
        setAllQueueResults(Array.isArray(allResults.jobs) ? allResults.jobs : []);
      } else {
        // If the call fails or the format is wrong, ensure it's an empty array
        setAllQueueResults(Array.isArray(allResults) ? allResults : []);
      }
    } catch (error) {
      console.error('Error loading all queue results:', error);
      // Ensure state is always an array even on error
      setAllQueueResults([]);
    }
  };

  const handleStartConsumer = async () => {
    setConsumerButtonLoading(true);
    try {
      const result = await startConsumer();
      console.log('Consumer started:', result);
      // Refresh status immediately
      const consumerData = await getConsumerStatus();
      setConsumerStatus(consumerData);
      // Load all queue results when consumer starts and refresh immediately
      await loadAllQueueResults();

      // Force refresh results multiple times to ensure they load
      setTimeout(async () => {
        await loadAllQueueResults();
      }, 1000);

      setTimeout(async () => {
        await loadAllQueueResults();
      }, 2000);

      setTimeout(async () => {
        await loadAllQueueResults();
      }, 3000);

      // Additional refresh to ensure results are visible
      setTimeout(async () => {
        await loadAllQueueResults();
      }, 5000);

      setTimeout(async () => {
        await loadAllQueueResults();
      }, 7000);
    } catch (error) {
      alert('Error iniciando el consumidor: ' + error.message);
    } finally {
      setConsumerButtonLoading(false);
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
      alert('Error deteniendo el consumidor: ' + error.message);
    }
  };

  const startAnalysis = async () => {
    const validSoftware = softwareList.filter(software => software.trim() !== '');
    if (validSoftware.length === 0) {
      alert('Por favor agregue al menos un software para analizar.');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setResults([]);

    // Simulate progress bar with max 4 seconds duration
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const increment = 25; // 100% / 4 intervals = 25% per interval
        const newProgress = prev + increment;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          setIsAnalyzing(false);
          return 100;
        }
        return newProgress;
      });
    }, 1000); // 1 second intervals

    try {
      // Send software list for async analysis
      const response = await analyzeSoftwareAsync(validSoftware, analysisParams);

      // Validate response structure
      if (!response || !response.job_ids || !Array.isArray(response.job_ids)) {
        throw new Error('Invalid response from server: missing job_ids array');
      }

      setAnalysisStatus({
        status: 'queued',
        jobIds: response.job_ids,
        estimatedTime: response.estimated_time,
        message: response.message
      });

      // Track jobs history with validation
      setJobsHistory(validSoftware.map((software, index) => ({
        jobId: response.job_ids[index] || `unknown-${index}`,
        keyword: software
      })));

      // Stop the loading after 4 seconds regardless
      setTimeout(() => {
        setIsAnalyzing(false);
        setProgress(100);
        clearInterval(progressInterval);
      }, 4000);

    } catch (error) {
      console.error('Error starting analysis:', error);
      setIsAnalyzing(false);
      setProgress(0); clearInterval(progressInterval);
      alert('Error iniciando el análisis: ' + error.message);
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
    <div className="async-software-analysis">      <div className="analysis-header">
      <h2>🔍 Análisis Asíncrono de Software</h2>
      <p>Analice múltiples software usando Kong Gateway + RabbitMQ para procesamiento asíncrono</p>
    </div>

      {/* Software Input - MOVED TO TOP */}
      <div className="software-input-section">
        <h3>📦 Lista de Software a Analizar</h3>
        {softwareList.map((software, index) => (
          <div key={index} className="software-input-row">            <input
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
                  setAnalysisParams({ ...analysisParams, includeCategories: categories });
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
                  setAnalysisParams({ ...analysisParams, includeCategories: categories });
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
        >          {isAnalyzing ? (
          <>
            <div className="spinner"></div>
            Analizando... ({Math.round(progress)}%)
          </>
        ) : (
          <>🚀 Iniciar Análisis Asíncrono</>
        )}
        </button>
      </div>

      {/* Queue Status */}
      {queueStatus && (<div className="queue-status">
        <h4>📊 Estado de la Cola RabbitMQ</h4>
        <div className="status-grid">
          <div className="status-item">
            <span className="label">Pendientes:</span>
            <span className="value pending">{queueStatus.pending_jobs || 0}</span>
          </div>
          <div className="status-item">
            <span className="label">Completados:</span>
            <span className="value completed">{allQueueResults.length || queueStatus.completed_jobs || 0}</span>
          </div>
          <div className="status-item">
            <span className="label">Estado:</span>
            <span className={`value status healthy`}>
              Saludable
            </span>
          </div>
        </div>

        {/* Visual Progress Indicators */}
        <div className="queue-visual">            <div className="queue-progress">
          <div className="progress-section">
            <div className="progress-label">Trabajos en Cola</div>
            <div className="progress-visual">
              {Array.from({ length: Math.max(queueStatus.pending_jobs || 0, 1) }).map((_, i) => (
                <div key={i} className={`job-dot ${i < (queueStatus.pending_jobs || 0) ? 'pending' : 'empty'}`}>
                </div>
              ))}
            </div>
          </div>

          <div className="progress-arrow"></div>

          <div className="progress-section">
            <div className="progress-label">Trabajos Completados</div>
            <div className="progress-visual">
              {Array.from({ length: Math.max(allQueueResults.length || queueStatus.completed_jobs || 0, 1) }).map((_, i) => (
                <div key={i} className={`job-dot ${i < (allQueueResults.length || queueStatus.completed_jobs || 0) ? 'completed' : 'empty'}`}>
                </div>
              ))}
            </div>
          </div>
        </div>
        </div>
      </div>
      )}

      {/* Consumer Control */}
      {consumerStatus && (<div className="consumer-control">
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
              <button
                onClick={handleStartConsumer}
                className="start-consumer-btn"
                disabled={consumerButtonLoading}
              >
                {consumerButtonLoading ? (
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                ) : (
                  'Iniciar Consumidor'
                )}
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
        </div>          <div className="consumer-info">
          <p>💡 <strong>Consejo:</strong> El consumidor debe estar ejecutándose para procesar automáticamente los trabajos de la cola.</p>
        </div>
      </div>
      )}

      {/* All Queue Results - Found Vulnerabilities from Queue Analysis */}
      <div className="all-queue-results">
        <div className="results-header">
          <h4>🔍 Vulnerabilidades Encontradas del Análisis de Cola</h4>
          <div className="results-summary">
            <button onClick={loadAllQueueResults} className="refresh-results-btn">
              🔄 Actualizar Resultados
            </button>
          </div>
        </div>

        {allQueueResults.length === 0 ? (
          <div className="no-results-message">
            <div className="no-results-content">
              <h5>📋 No se Encontraron Resultados de Vulnerabilidades</h5>
              <p>Ejecute algún análisis de software usando la sección de Análisis Asíncrono para ver los resultados de vulnerabilidades aquí.</p>
              <div className="summary-stats">
                <div className="stat-card">
                  <div className="stat-icon">📦</div>
                  <div className="stat-number">0</div>
                  <div className="stat-label">Total de Trabajos</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">✅</div>
                  <div className="stat-number">0</div>
                  <div className="stat-label">Completados</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">⏳</div>
                  <div className="stat-number">0</div>
                  <div className="stat-label">In Progress</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">🚨</div>                    <div className="stat-number">0</div>
                  <div className="stat-label">Vulnerabilidades Encontradas</div>
                </div>
              </div>

              <div className="vulnerabilities-per-job">
                <h6>Vulnerabilidades por Trabajo</h6>
                <p>No hay trabajos para mostrar.</p>
              </div>
            </div>
          </div>
        ) : (
          <>              <div className="summary-stats">
            <div className="stat-card">
              <div className="stat-icon">📦</div>
              <div className="stat-number">{allQueueResults.length}</div>
              <div className="stat-label">Total de Trabajos</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-number">{allQueueResults.length}</div>
              <div className="stat-label">Completados</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">⏳</div>
              <div className="stat-number">0</div>
              <div className="stat-label">En Progreso</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🚨</div>
              <div className="stat-number">
                {Array.isArray(allQueueResults) ? allQueueResults.reduce((total, job) => total + (job.total_results || 0), 0) : 0}
              </div>
              <div className="stat-label">Vulnerabilidades Encontradas</div>
            </div>
          </div>

            <div className="vulnerabilities-per-job">
              <h6>Vulnerabilidades por Trabajo</h6>
              <div className="queue-results-grid">
                {Array.isArray(allQueueResults) && allQueueResults.map((job, index) => {
                  const totalVulnerabilities = job.total_results || 0;
                  const vulnerabilities = job.vulnerabilities || [];

                  // Calculate severity counts
                  const severityCounts = vulnerabilities.reduce((counts, vuln) => {
                    const severity = vuln.cve?.metrics?.cvssMetricV2?.[0]?.baseSeverity || 'DESCONOCIDO';
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
                              ⏰ {job.processed_at ? new Date(job.processed_at * 1000).toLocaleString() : 'Recently'}
                            </span>
                          </div>
                        </div>                          <div className="results-count">
                          <span className="total-count">{totalVulnerabilities} vulnerabilidades</span>
                        </div>
                      </div>

                      <div className="severity-summary">
                        <div className="severity-stats">                            {severityCounts.HIGH > 0 && (
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
                      </div>                        {vulnerabilities.length > 0 && (
                        <div className="vulnerabilities-preview">
                          <h6>🔸 Vista Previa de Vulnerabilidades:</h6>
                          <div className="vuln-preview-list">
                            {vulnerabilities.slice(0, 3).map((vuln, vIndex) => {
                              const cve = vuln.cve || {};
                              const severity = cve.metrics?.cvssMetricV2?.[0]?.baseSeverity || 'DESCONOCIDO';
                              const score = cve.metrics?.cvssMetricV2?.[0]?.cvssData?.baseScore || 'N/A';
                              const description = cve.descriptions?.[0]?.value || 'No description';

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
                            })}                              {vulnerabilities.length > 3 && (
                              <div className="more-vulns-indicator">
                                <span>... y {vulnerabilities.length - 3} vulnerabilidades más</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="card-footer">
                        <div className="processed-info">                            <span className="processed-via">
                          🚀 Procesado via: {job.processed_via || 'queue_consumer'}
                        </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>      {/* DB History Section - Renamed to Reportes de Análisis */}
      <div className="db-history-section" style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
        <h4>📜 Reportes de Análisis (Historial)</h4>
        <div className="history-list">
          {dbHistory.length === 0 ? (
            <p>No hay reportes de análisis registrados en la base de datos.</p>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped">
                <thead>
                  <tr>
                    <th>ID Trabajo</th>
                    <th>Software (Keyword)</th>
                    <th>Estado</th>
                    <th>Resultados</th>
                    <th>Fecha de Análisis</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(dbHistory) && dbHistory.map((job) => (
                    <tr key={job.job_id}>
                      <td>{job.job_id.substring(0, 8)}...</td>
                      <td>{job.keyword}</td>
                      <td>
                        <span className={`badge ${job.status === 'completed' ? 'bg-success' : 'bg-warning'}`}>
                          {job.status === 'completed' ? 'Completado' : job.status}
                        </span>
                      </td>
                      <td>{job.total_results || 0} vulnerabilidades</td>
                      <td>{new Date(job.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
