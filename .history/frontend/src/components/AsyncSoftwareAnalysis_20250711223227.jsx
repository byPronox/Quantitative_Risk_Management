import React, { useState, useEffect } from 'react';
import { 
  analyzeSoftwareAsync, 
  getQueueStatus, 
  pollAnalysisResults,
  startConsumer,
  stopConsumer,
  getConsumerStatus
} from '../services/nvd';
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
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

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

    } catch (error) {
      console.error('Error starting analysis:', error);
      setIsAnalyzing(false);
      alert('Error al iniciar el análisis: ' + error.message);
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
    </div>
  );
}
