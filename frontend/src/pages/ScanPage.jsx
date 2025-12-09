import React, { useState, useEffect } from 'react';
import { backendApi } from '../services/api';
import '../styles/ScanPage.css';

export default function ScanPage() {
  const [target, setTarget] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const [error, setError] = useState(null);
  const [showDocs, setShowDocs] = useState(false);

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
      setError('Por favor introduce un objetivo para escanear');
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
      setError(error.response?.data?.detail || error.response?.data?.error || 'Escaneo falló');
      console.error('Scan error:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const formatScanResults = (results) => {
    if (!results) return null; return {
      host: results.host || results.ip || 'Desconocido',
      status: results.status || 'Desconocido',
      ports: results.ports || [],
      services: results.services || [],
      vulnerabilities: results.vulnerabilities || [],
      os: results.os || 'Desconocido',
      summary: results.summary || null
    };
  };

  const getSeverityColor = (severity) => {
    if (!severity) return '#6c757d';
    switch (String(severity).toLowerCase()) {
      case 'critical': return '#8b0000';
      case 'high': return '#dc3545';
      case 'medium': return '#fd7e14';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getRiskColor = (category) => {
    if (!category) return '#6c757d';
    switch (String(category).toLowerCase()) {
      case 'muy baja': return '#6c757d';
      case 'baja': return '#28a745';
      case 'media': return '#ffc107';
      case 'alta': return '#fd7e14';
      case 'muy alta': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const buildPersonalizedRemediation = (vuln) => {
    // Start with backend suggestions (already helpful)
    const base = Array.isArray(vuln.treatment?.remediation) ? [...vuln.treatment.remediation] : [];
    const extras = [];    // If CVE present suggest applying vendor patch with link to NVD
    if (vuln.cve) {
      extras.push(`Ver detalles y parche en NVD: https://nvd.nist.gov/vuln/detail/${vuln.cve}`);
      extras.push('Priorizar parcheo según políticas de mantenimiento (ventana urgente si riesgo Alta/Muy alta).');
    }

    // If product or port suggest configuration/action tailored
    const product = vuln.context?.product || vuln.product || '';
    const port = vuln.context?.port || '';
    if (product) {
      extras.push(`Revisar versión y configuración de ${product}. Comprobar changelog de seguridad del proveedor.`);
    }
    if (port) {
      extras.push(`Restringir acceso al puerto ${port} desde Internet mediante firewall/ACL si no es necesario públicamente.`);
    }

    // If classification DB and high risk propose isolate and restore steps
    if (String(vuln.classification).toLowerCase().includes('bases de datos')) {
      if (vuln.risk?.score > 70) {
        extras.unshift('Aislar la base de datos de la red pública y activar respaldo/restauración segura.');
      } else {
        extras.unshift('Revisar privilegios de base de datos y cifrado en tránsito y reposo.');
      }
    }

    // If severity unknown but outputs indicate "server header" suggest update server software
    const titleLower = String(vuln.title || '').toLowerCase();
    if (titleLower.includes('server-header') || titleLower.includes('http')) {
      extras.push('Revisar y actualizar software del servidor web y ajustar cabeceras de seguridad (HSTS, X-Content-Type-Options, CSP).');
    }

    // Avoid duplicate lines
    const combined = [...base, ...extras].filter((v, i, a) => v && a.indexOf(v) === i);
    return combined.length > 0 ? combined : ['Revisión manual recomendada por el equipo de seguridad.'];
  };

  const exportCSV = () => {
    if (!scanResults) return;
    const formatted = formatScanResults(scanResults);
    const rows = [];
    // Header
    rows.push([
      'host',
      'status',
      'port',
      'service',
      'product',
      'classification',
      'vuln_id',
      'title',
      'cve',
      'cvss_base',
      'risk_score',
      'risk_category',
      'treatment',
      'treatment_reason',
      'treatment_remediation',
      'nvd_url'
    ]);

    if ((formatted.vulnerabilities || []).length === 0) {
      rows.push([
        formatted.host,
        formatted.status,
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        ''
      ]);
    } else {
      formatted.vulnerabilities.forEach(v => {
        const port = v.context?.port || '';
        const service = v.context?.product || '';
        const classification = v.classification || '';
        const vulnId = v.id || '';
        const title = v.title ? v.title.replace(/\n/g, ' ').replace(/"/g, '""') : '';
        const cve = v.cve || (v.nvd && v.nvd.id) || '';
        const cvss = v.cvssBase || (v.nvd && (v.nvd.impact?.baseMetricV3?.cvssV3?.baseScore || '')) || '';
        const riskScore = v.risk?.score ?? '';
        const riskCat = v.risk?.category || '';
        const treatment = v.treatment?.treatment || '';
        const reason = v.treatment?.reason ? v.treatment.reason.replace(/\n/g, ' ').replace(/"/g, '""') : '';
        const remediation = Array.isArray(v.treatment?.remediation) ? v.treatment.remediation.join('; ').replace(/"/g, '""') : '';
        const nvdUrl = cve ? `https://nvd.nist.gov/vuln/detail/${cve}` : '';

        rows.push([
          formatted.host,
          formatted.status,
          port,
          v.context?.type || '',
          service,
          classification,
          vulnId,
          title,
          cve,
          cvss,
          riskScore,
          riskCat,
          treatment,
          reason,
          remediation,
          nvdUrl
        ]);
      });
    }

    const csvContent = rows.map(r => r.map(field => `"${String(field ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `escaneo_${formatted.host || 'resultado'}_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };



  return (
    <div className="scan-page" style={{ padding: '20px', maxWidth: 1100, margin: '0 auto' }}>

      {/* 1. Scan Input Section (Prioritized) */}
      <div className="scan-config" style={{ marginBottom: '24px', padding: '24px', borderRadius: '12px', background: '#ffffff', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', border: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ margin: 0, color: '#2d3748', fontSize: '1.5rem' }}>🚀 Escáner de Vulnerabilidades</h2>
          <button
            onClick={() => setShowDocs(!showDocs)}
            style={{
              background: 'none',
              border: '1px solid #cbd5e0',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              color: '#4a5568',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {showDocs ? 'Ocultar Ayuda' : '📖 Ver Ayuda / Documentación'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="text"
            id="target"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Ingrese IP (ej: 192.168.1.1) o Dominio (ej: ejemplo.com)"
            style={{ flex: 1, padding: '12px 16px', borderRadius: 8, border: '2px solid #e2e8f0', fontSize: '1.1em' }}
            aria-label="IP o dominio objetivo"
          />
          <button
            onClick={startScan}
            disabled={isScanning || !target.trim()}
            style={{
              padding: '12px 24px',
              borderRadius: 8,
              background: isScanning ? '#a0aec0' : '#3182ce',
              color: '#fff',
              border: 'none',
              cursor: isScanning ? 'default' : 'pointer',
              fontSize: '1.1em',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(49, 130, 206, 0.3)'
            }}
            aria-label="Iniciar escaneo de red"
          >
            {isScanning ? 'Escaneando...' : 'Escanear Ahora'}
          </button>
          <button
            onClick={exportCSV}
            disabled={!scanResults}
            style={{ padding: '12px 16px', borderRadius: 8, background: '#38b2ac', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
            aria-label="Exportar resultados del escaneo a CSV"
          >
            ⤓ CSV
          </button>
        </div>
        <p style={{ marginTop: 12, color: '#718096', fontSize: '0.9em' }}>
          ℹ️ El escaneo puede tardar varios minutos. Por favor no cierre la ventana.
        </p>
      </div>

      {/* 2. Collapsible Documentation Section */}
      {showDocs && (
        <div className="docs-container" style={{ animation: 'fadeIn 0.3s ease-in-out' }}>

          {/* Guía Básica */}
          <section style={{ background: '#fff', padding: '24px', borderRadius: '12px', marginBottom: '24px', borderLeft: '6px solid #4299e1', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#2b6cb0' }}>📘 Guía Rápida: ¿Qué estoy viendo?</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>

              {/* Para el Gerente */}
              <div style={{ background: '#ebf8ff', padding: '16px', borderRadius: '8px' }}>
                <strong style={{ color: '#2c5282', display: 'block', marginBottom: '8px' }}>👔 Para el Gerente (No Técnico)</strong>
                <p style={{ fontSize: '0.95em', color: '#2d3748', lineHeight: '1.6' }}>
                  Piense en este escáner como un <strong>inspector de edificios</strong> digital.
                  <br />Revisa su "casa" (servidor) buscando:
                  <ul style={{ paddingLeft: '20px', marginTop: '8px' }}>
                    <li>🚪 <strong>Puertas Abiertas (Puertos):</strong> Entradas que dejó sin llave.</li>
                    <li>🪟 <strong>Ventanas Rotas (Vulnerabilidades):</strong> Fallos que un ladrón podría usar para entrar.</li>
                  </ul>
                  <strong>Su meta:</strong> Mantener las puertas cerradas y arreglar las ventanas rotas.
                </p>
              </div>

              {/* Para el Técnico */}
              <div style={{ background: '#f7fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <strong style={{ color: '#4a5568', display: 'block', marginBottom: '8px' }}>🛠️ Para el Ingeniero (Técnico)</strong>
                <p style={{ fontSize: '0.95em', color: '#4a5568', lineHeight: '1.6' }}>
                  Esta herramienta ejecuta <strong>Nmap</strong> con scripts de detección de vulnerabilidades (NSE).
                  <br />Identifica servicios expuestos, versiones de software y CVEs conocidos.
                  <br />El puntaje de riesgo pondera: <strong>CVSS Base (60%)</strong> + <strong>Exposición Pública (30%)</strong> + <strong>Densidad de Fallos (10%)</strong>.
                </p>
              </div>
            </div>
          </section>

          {/* Diccionario y Modelo */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginBottom: '24px' }}>

            {/* Diccionario */}
            <section style={{ background: '#fff', padding: '20px', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
              <h3 style={{ margin: '0 0 16px 0', color: '#2d3748' }}>📖 Glosario Esencial</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <strong style={{ color: '#e53e3e' }}>Vulnerabilidad (CVE)</strong>
                  <p style={{ fontSize: '0.9em', color: '#718096', margin: '4px 0 0 0' }}>Fallo de seguridad reconocido globalmente. Es como tener una copia de su llave circulando en internet.</p>
                </div>
                <div>
                  <strong style={{ color: '#d69e2e' }}>CVSS (0-10)</strong>
                  <p style={{ fontSize: '0.9em', color: '#718096', margin: '4px 0 0 0' }}>Estándar industrial para medir la gravedad. 10 es crítico (actuar ya), 0 es seguro.</p>
                </div>
              </div>
            </section>

            {/* Modelo de Riesgo Simplificado */}
            <section style={{ background: '#2d3748', color: 'white', padding: '20px', borderRadius: '12px' }}>
              <h3 style={{ margin: '0 0 16px 0', color: '#fff' }}>⚖️ ¿Cómo calculamos el riesgo?</h3>
              <div style={{ fontSize: '0.95em', lineHeight: '1.6', color: '#cbd5e0' }}>
                No usamos solo el CVSS. Nuestro algoritmo es contextual:
                <br /><br />
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ background: '#fc8181', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.8em' }}>60%</span>
                  <span><strong>Gravedad (CVSS):</strong> ¿Qué tan peligroso es el fallo?</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ background: '#63b3ed', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.8em' }}>30%</span>
                  <span><strong>Exposición:</strong> ¿Está abierto a internet?</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ background: '#f6ad55', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.8em' }}>10%</span>
                  <span><strong>Cantidad:</strong> ¿Hay muchos fallos juntos?</span>
                </div>
              </div>
            </section>
          </div>
        </div>
      )}

      {/* Results */}
      {error && <div style={{ marginBottom: 12, color: '#c82333' }}>{error}</div>}

      {scanResults && (
        <div className="scan-results">
          <h3 style={{ marginTop: 0 }}>📊 Resultados del Escaneo</h3>
          {(() => {
            const formatted = formatScanResults(scanResults);
            return (
              <>
                <div style={{ marginBottom: '12px', background: '#f8f9fa', padding: '12px', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e9ecef', paddingBottom: '8px', marginBottom: '8px' }}>
                    <div>
                      <h4 style={{ margin: 0 }}>🎯 Objetivo: {formatted.host}</h4>
                      <div style={{ color: '#666' }}>Estado: {formatted.status} • OS: {formatted.os}</div>
                    </div>
                    {formatted.summary && (
                      <div style={{ textAlign: 'right' }}>
                        <div><strong>Vulnerabilidades:</strong> {formatted.summary.total_vulnerabilities}</div>
                        <div><strong>Máx:</strong> {formatted.summary.max_score} • <strong>Prom:</strong> {formatted.summary.average_score}</div>
                        <div style={{ marginTop: 6 }}><strong>Categoria aggregate:</strong> <span style={{ color: getRiskColor(formatted.summary.aggregate_category), fontWeight: 700 }}>{formatted.summary.aggregate_category}</span></div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Ports */}
                {formatted.ports.length > 0 && (
                  <div style={{ marginBottom: 16, background: '#f8f9fa', padding: '12px', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                    <h4 style={{ marginBottom: 8 }}>Puertos abiertos ({formatted.ports.length})</h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: '8px 0' }}>
                      {formatted.ports.map((p, i) => (
                        <div key={i} style={{ background: '#fff', padding: '8px 10px', borderRadius: 8, boxShadow: '0 1px 2px rgba(0,0,0,0.04)', minWidth: 180 }}>
                          <div style={{ fontWeight: 700 }}>{p.port}/{p.protocol}</div>
                          <div style={{ color: '#666', fontSize: 13 }}>{p.service} {p.product ? `• ${p.product}` : ''}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Vulnerabilities list - improved layout */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {formatted.vulnerabilities.map((vuln, idx) => (
                    <div key={idx} style={{ background: '#fff', padding: 12, borderRadius: 8, display: 'flex', gap: 12, boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
                      <div style={{ width: 160, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <div style={{ background: getRiskColor(vuln.risk?.category), color: '#fff', padding: '6px 8px', borderRadius: 6, fontWeight: 700 }}>
                            {vuln.risk?.category || 'N/A'}
                          </div>
                          <div style={{ background: getSeverityColor(vuln.severity), color: '#fff', padding: '6px 8px', borderRadius: 6 }}>
                            {vuln.severity?.toUpperCase() || 'DESCONOCIDO'}
                          </div>
                        </div>

                        <div style={{ fontWeight: 700, fontSize: 14 }}>{vuln.title}</div>
                        <div style={{ color: '#666', fontSize: 13 }}>
                          <div><strong>Activo:</strong> {vuln.classification || (vuln.context?.type || 'N/A')}</div>
                          <div><strong>Puerto:</strong> {vuln.context?.port || 'N/A'}</div>
                          <div><strong>Producto:</strong> {vuln.context?.product || 'N/A'}</div>
                          <div><strong>CVE:</strong> {vuln.cve || 'N/A'}</div>
                          <div><strong>Puntaje:</strong> {vuln.risk?.score ?? 'N/A'}</div>
                        </div>
                      </div>

                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {vuln.treatment?.report ? (
                          <div dangerouslySetInnerHTML={{ __html: vuln.treatment.report }} />
                        ) : (
                          <>
                            <div style={{ color: '#333' }}>
                              <strong>Descripción:</strong>
                              <div style={{ marginTop: 6, whiteSpace: 'pre-wrap', color: '#444' }}>
                                {vuln.description || 'No hay descripción detallada disponible.'}
                              </div>
                            </div>

                            {/* Treatment and personalized remediation */}
                            <div style={{ marginTop: 6, background: '#fbfcfe', padding: 10, borderRadius: 6 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                  <strong>Tratamiento recomendado:</strong> <span style={{ textTransform: 'capitalize' }}>{vuln.treatment?.treatment || 'N/A'}</span>
                                </div>
                                <div style={{ color: '#666' }}>Puntaje: <strong>{vuln.risk?.score ?? 'N/A'}</strong></div>
                              </div>

                              <div style={{ marginTop: 8 }}>
                                <strong>Motivo:</strong>
                                <div style={{ marginTop: 6 }}>{vuln.treatment?.reason || 'No se proporcionó motivo.'}</div>
                              </div>

                              <div style={{ marginTop: 8 }}>
                                <strong>Remediación sugerida:</strong>
                                <ul style={{ marginTop: 6 }}>
                                  {buildPersonalizedRemediation(vuln).map((r, i) => <li key={i}>{r}</li>)}
                                </ul>
                              </div>

                              {vuln.cve && (
                                <div style={{ marginTop: 8 }}>
                                  <a href={`https://nvd.nist.gov/vuln/detail/${vuln.cve}`} target="_blank" rel="noreferrer">Ver en NVD: {vuln.cve}</a>
                                </div>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
}

/* Small presentational badge component */
function Badge({ label, color }) {
  return (
    <span style={{
      background: color,
      color: '#fff',
      padding: '6px 10px',
      borderRadius: 6,
      fontWeight: 700,
      textTransform: 'capitalize'
    }}>{label}</span>
  );
}
