import React, { useState, useEffect } from 'react';
import api, { backendApi } from '../services/api';
import '../styles/ScannerModule.css';

export default function ScannerModule() {
  const [target, setTarget] = useState('');
  const [currentJobId, setCurrentJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [scanResults, setScanResults] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  
  // Flow tracking state
  const [flowSteps, setFlowSteps] = useState([
    { id: 1, name: 'Frontend', status: 'idle', icon: '🖥️', detail: '' },
    { id: 2, name: 'Kong Gateway', status: 'idle', icon: '🚪', detail: '' },
    { id: 3, name: 'Backend API', status: 'idle', icon: '⚙️', detail: '' },
    { id: 4, name: 'RabbitMQ', status: 'idle', icon: '🐰', detail: '' },
    { id: 5, name: 'NMAP Worker', status: 'idle', icon: '🔍', detail: '' },
    { id: 6, name: 'PostgreSQL', status: 'idle', icon: '🗄️', detail: '' },
  ]);

  const updateFlowStep = (stepId, status, detail = '') => {
    setFlowSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, status, detail } : step
    ));
  };

  const resetFlow = () => {
    setFlowSteps(prev => prev.map(step => ({ ...step, status: 'idle', detail: '' })));
  };

  // Get Kong URL from environment
  const getKongUrl = () => {
    return import.meta.env.VITE_API_URL || 'http://localhost:8080';
  };

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

  // Step 1: Submit scan through Kong -> Backend -> RabbitMQ
  const submitToQueue = async () => {
    if (!target.trim()) {
      setError('Por favor introduzca un objetivo para escanear');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    setScanResults(null);
    setJobStatus(null);
    resetFlow();

    try {
      // Step 1: Frontend initiates
      updateFlowStep(1, 'active', 'Iniciando solicitud...');
      await new Promise(r => setTimeout(r, 300));
      updateFlowStep(1, 'completed', `Enviando IP: ${target}`);

      // Step 2: Kong Gateway
      updateFlowStep(2, 'active', `Conectando a ${getKongUrl()}...`);
      await new Promise(r => setTimeout(r, 300));
      
      // Make the actual API call through Kong
      const kongUrl = getKongUrl();
      console.log(`📤 Sending to Kong Gateway: ${kongUrl}/api/v1/scan/async`);
      
      updateFlowStep(2, 'completed', 'Ruta: /api/v1/scan/async');
      
      // Step 3: Backend receives
      updateFlowStep(3, 'active', 'Backend procesando...');
      
      const response = await api.post('/api/v1/scan/async', null, {
        params: { target: target.trim() }
      });

      const { job_id, status, message } = response.data;
      
      if (!job_id) {
        throw new Error('No se recibió ID de trabajo');
      }

      updateFlowStep(3, 'completed', `Job creado: ${job_id.slice(0, 8)}...`);

      // Step 4: RabbitMQ
      updateFlowStep(4, 'active', 'Publicando en cola...');
      await new Promise(r => setTimeout(r, 300));
      updateFlowStep(4, 'completed', 'Cola: nmap_scan_queue');

      // Step 5: NMAP Worker waiting
      updateFlowStep(5, 'pending', 'Esperando worker...');

      // Step 6: PostgreSQL
      updateFlowStep(6, 'completed', 'Job guardado en DB');

      setCurrentJobId(job_id);
      setJobStatus(status);
      setSuccessMessage(`✅ Trabajo enviado exitosamente!\n📋 Job ID: ${job_id}\n🐰 Cola: nmap_scan_queue`);
      
      console.log(`✅ Scan job submitted: ${job_id}`);
      console.log(`   Flow: Frontend → Kong (${kongUrl}) → Backend → RabbitMQ → PostgreSQL`);
      
      loadScanHistory();
      
    } catch (error) {
      console.error('❌ Submit error:', error);
      updateFlowStep(2, 'error', 'Error de conexión');
      setError(error.response?.data?.detail || error.message || 'Error al enviar a la cola');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 2: Poll/Consume results
  const consumeResults = async () => {
    if (!currentJobId) {
      setError('No hay trabajo pendiente. Primero envíe un escaneo a la cola.');
      return;
    }

    setIsPolling(true);
    setError(null);
    setSuccessMessage(null);

    try {
      updateFlowStep(1, 'active', 'Consultando estado...');
      updateFlowStep(2, 'active', 'Via Kong Gateway...');
      
      const response = await api.get(`/api/v1/scan/status/${currentJobId}`);
      const { status, result, error: jobError, target: jobTarget } = response.data;
      
      updateFlowStep(1, 'completed', 'Respuesta recibida');
      updateFlowStep(2, 'completed', 'Kong OK');
      updateFlowStep(3, 'completed', 'Backend OK');
      
      setJobStatus(status);
      
      if (status === 'completed') {
        updateFlowStep(5, 'completed', 'Escaneo finalizado');
        updateFlowStep(6, 'completed', 'Resultado en DB');
        setScanResults(result);
        setSuccessMessage(`✅ Escaneo completado para ${jobTarget}`);
        loadScanHistory();
      } else if (status === 'failed') {
        updateFlowStep(5, 'error', 'Escaneo falló');
        setError(`❌ Escaneo falló: ${jobError || 'Error desconocido'}`);
      } else if (status === 'processing') {
        updateFlowStep(5, 'active', 'Worker ejecutando nmap...');
        setSuccessMessage(`⏳ Escaneo en progreso...\n🔍 NMAP Worker procesando: ${jobTarget}`);
      } else if (status === 'queued') {
        updateFlowStep(4, 'active', 'Mensaje en cola');
        updateFlowStep(5, 'pending', 'Esperando worker');
        setSuccessMessage(`📋 En cola RabbitMQ...\n⏳ Esperando que un worker tome el trabajo`);
      }
      
    } catch (error) {
      setError(error.response?.data?.detail || error.message || 'Error al consultar estado');
    } finally {
      setIsPolling(false);
    }
  };

  // Auto-poll
  const startAutoPolling = async () => {
    if (!currentJobId) {
      setError('No hay trabajo pendiente.');
      return;
    }

    setIsPolling(true);
    setError(null);
    setSuccessMessage('🔄 Esperando resultados automáticamente...');

    const maxAttempts = 60;
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const response = await api.get(`/api/v1/scan/status/${currentJobId}`);
        const { status, result, error: jobError, target: jobTarget } = response.data;
        
        setJobStatus(status);
        
        if (status === 'completed') {
          updateFlowStep(5, 'completed', 'Escaneo finalizado');
          updateFlowStep(6, 'completed', 'Resultado guardado');
          setScanResults(result);
          setSuccessMessage(`✅ Escaneo completado para ${jobTarget}`);
          loadScanHistory();
          break;
        } else if (status === 'failed') {
          updateFlowStep(5, 'error', 'Error en escaneo');
          setError(`❌ Escaneo falló: ${jobError || 'Error desconocido'}`);
          break;
        } else if (status === 'processing') {
          updateFlowStep(5, 'active', `Escaneando... (${attempts + 1}/${maxAttempts})`);
          setSuccessMessage(`⏳ NMAP Worker escaneando...\n🔍 Intento ${attempts + 1}/${maxAttempts}`);
        } else {
          updateFlowStep(4, 'active', 'En cola RabbitMQ');
          setSuccessMessage(`📋 En cola... (${attempts + 1}/${maxAttempts})`);
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        attempts++;
        
      } catch (err) {
        await new Promise(resolve => setTimeout(resolve, 5000));
        attempts++;
      }
    }

    if (attempts >= maxAttempts) {
      setError('⏰ Tiempo de espera agotado.');
    }

    setIsPolling(false);
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': case 'muy alta': return '#dc3545';
      case 'high': case 'alta': return '#fd7e14';
      case 'medium': case 'media': return '#ffc107';
      case 'low': case 'baja': return '#28a745';
      case 'muy baja': return '#17a2b8';
      default: return '#6c757d';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#28a745';
      case 'processing': return '#ffc107';
      case 'queued': return '#17a2b8';
      case 'failed': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getFlowStepClass = (status) => {
    switch (status) {
      case 'active': return 'flow-step-active';
      case 'completed': return 'flow-step-completed';
      case 'pending': return 'flow-step-pending';
      case 'error': return 'flow-step-error';
      default: return 'flow-step-idle';
    }
  };

  return (
    <div className="scanner-module">
      <div className="scanner-header">
        <h2>🔍 Escáner de Red NMAP</h2>
        <p>Sistema Distribuido con Kong Gateway y RabbitMQ</p>
        <div className="api-info">
          <span>🚪 Kong: <code>{getKongUrl()}</code></span>
          <span>🐰 Queue: <code>nmap_scan_queue</code></span>
        </div>
      </div>

      {/* Flow Visualization */}
      <div className="flow-visualization">
        <h3>📊 Flujo del Sistema</h3>
        <div className="flow-steps">
          {flowSteps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className={`flow-step ${getFlowStepClass(step.status)}`}>
                <span className="flow-icon">{step.icon}</span>
                <span className="flow-name">{step.name}</span>
                {step.detail && <span className="flow-detail">{step.detail}</span>}
              </div>
              {index < flowSteps.length - 1 && (
                <div className={`flow-arrow ${step.status === 'completed' ? 'arrow-active' : ''}`}>→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step 1: Submit to Queue */}
      <div className="scanner-config">
        <h3>📤 Paso 1: Enviar a Cola via Kong Gateway</h3>
        <div className="config-form">
          <div className="form-group">
            <label htmlFor="target">Objetivo (IP, Dominio, o Red):</label>
            <input
              type="text"
              id="target"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="ej: 192.168.1.1, scanme.nmap.org, 10.0.0.0/24"
              className="target-input"
              disabled={isSubmitting || isPolling}
            />
          </div>

          <button
            onClick={submitToQueue}
            disabled={isSubmitting || isPolling || !target.trim()}
            className={`scan-button submit-button ${isSubmitting ? 'loading' : ''}`}
          >
            {isSubmitting ? (
              <>
                <div className="spinner"></div>
                Enviando via Kong...
              </>
            ) : (
              '📤 Enviar a Cola (Kong → Backend → RabbitMQ)'
            )}
          </button>
        </div>
      </div>

      {/* Current Job Status */}
      {currentJobId && (
        <div className="job-status-section">
          <h3>📋 Trabajo en Proceso</h3>
          <div className="job-info">
            <p><strong>Job ID:</strong> <code>{currentJobId}</code></p>
            <p><strong>Target:</strong> <code>{target}</code></p>
            <p>
              <strong>Estado:</strong> 
              <span 
                className="status-indicator"
                style={{ backgroundColor: getStatusColor(jobStatus), marginLeft: '8px', padding: '4px 12px', borderRadius: '4px', color: 'white' }}
              >
                {jobStatus || 'Desconocido'}
              </span>
            </p>
          </div>
        </div>
      )}

      {/* Step 2: Consume Results */}
      <div className="scanner-config">
        <h3>📥 Paso 2: Consumir Resultados</h3>
        <div className="button-group">
          <button
            onClick={consumeResults}
            disabled={!currentJobId || isPolling || isSubmitting}
            className={`scan-button consume-button ${isPolling ? 'loading' : ''}`}
          >
            {isPolling ? (
              <>
                <div className="spinner"></div>
                Consultando via Kong...
              </>
            ) : (
              '🔍 Consultar Estado (Kong → Backend → PostgreSQL)'
            )}
          </button>

          <button
            onClick={startAutoPolling}
            disabled={!currentJobId || isPolling || isSubmitting || jobStatus === 'completed'}
            className={`scan-button auto-poll-button ${isPolling ? 'loading' : ''}`}
          >
            🔄 Esperar Automáticamente
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <pre>{error}</pre>
        </div>
      )}

      {successMessage && (
        <div className="success-message">
          <pre>{successMessage}</pre>
        </div>
      )}

      {/* Scan Results */}
      {scanResults && (
        <div className="scan-results">
          <h3>📊 Resultados del Escaneo</h3>
          <div className="results-content">
            <div className="host-info">
              <h4>🎯 Objetivo: {scanResults.host || scanResults.target || target}</h4>
              <p><strong>Estado:</strong> {scanResults.state || scanResults.status || 'Completado'}</p>
              {scanResults.os && <p><strong>SO Detectado:</strong> {scanResults.os}</p>}
              {scanResults.scanDuration && <p><strong>Duración:</strong> {scanResults.scanDuration}</p>}
            </div>

            {scanResults.ports && scanResults.ports.length > 0 && (
              <div className="ports-section">
                <h4>🔌 Puertos Abiertos ({scanResults.ports.length})</h4>
                <div className="ports-grid">
                  {scanResults.ports.map((port, index) => (
                    <div key={index} className="port-item">
                      <span className="port-number">{port.port || port.portid}</span>
                      <span className="port-state">{port.state}</span>
                      <span className="port-service">{port.service || port.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {scanResults.vulnerabilities && scanResults.vulnerabilities.length > 0 && (
              <div className="vulnerabilities-section">
                <h4>🚨 Vulnerabilidades ({scanResults.vulnerabilities.length})</h4>
                <div className="vuln-list">
                  {scanResults.vulnerabilities.map((vuln, index) => (
                    <div key={index} className="vuln-item">
                      <div className="vuln-header">
                        <span
                          className="severity-badge"
                          style={{ backgroundColor: getSeverityColor(vuln.severity || vuln.riskCategory) }}
                        >
                          {(vuln.severity || vuln.riskCategory || 'N/A').toUpperCase()}
                        </span>
                        <span className="vuln-title">{vuln.title || vuln.id || 'Vulnerabilidad'}</span>
                      </div>
                      <p className="vuln-description">{vuln.description || 'Sin descripción'}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(!scanResults.vulnerabilities || scanResults.vulnerabilities.length === 0) && (
              <div className="no-vulnerabilities">
                <span className="check-icon">✅</span>
                <p>No se encontraron vulnerabilidades críticas</p>
              </div>
            )}

            <details className="raw-results">
              <summary>🔧 Ver respuesta JSON completa</summary>
              <pre>{JSON.stringify(scanResults, null, 2)}</pre>
            </details>
          </div>
        </div>
      )}

      {/* Scan History */}
      <div className="scan-history">
        <h3>📋 Historial de Escaneos (PostgreSQL)</h3>
        <button onClick={loadScanHistory} className="refresh-button">🔄 Refrescar</button>
        
        {scanHistory.length > 0 ? (
          <div className="history-list">
            {scanHistory.slice(0, 10).map((scan) => (
              <div 
                key={scan.id || scan.job_id} 
                className="history-item"
                onClick={() => {
                  setCurrentJobId(scan.job_id);
                  setJobStatus(scan.status);
                  if (scan.result) setScanResults(scan.result);
                }}
              >
                <div className="history-header">
                  <span className="scan-target">{scan.target}</span>
                  <span className="scan-job-id">ID: {scan.job_id?.slice(0, 8)}...</span>
                  <span className="scan-time">
                    {scan.created_at ? new Date(scan.created_at).toLocaleString() : 'N/A'}
                  </span>
                </div>
                <div className="history-status">
                  <span className="status-badge" style={{ backgroundColor: getStatusColor(scan.status), color: 'white', padding: '2px 8px', borderRadius: '4px' }}>
                    {scan.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-history">No hay escaneos previos en la base de datos</p>
        )}
      </div>
    </div>
  );
}
