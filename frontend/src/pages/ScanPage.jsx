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
      setError(error.response?.data?.detail || error.response?.data?.error || 'Scan falló');
      console.error('Scan error:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const formatScanResults = (results) => {
    if (!results) return null;

    return {
      host: results.host || results.ip || 'Unknown',
      status: results.status || 'Unknown',
      ports: results.ports || [],
      services: results.services || [],
      vulnerabilities: results.vulnerabilities || [],
      os: results.os || 'Unknown',
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
    const extras = [];

    // If CVE present suggest applying vendor patch with link to NVD
    if (vuln.cve) {
      extras.push(`Ver detalles y parche en NVD: https://nvd.nist.gov/vuln/detail/${vuln.cve}`);
      extras.push('Priorizar parcheo según politicas de mantenimiento (ventana urgente si riesgo Alta/Muy alta).');
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
    a.download = `scan_${formatted.host || 'result'}_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="scan-page" style={{ padding: '20px', maxWidth: 1100, margin: '0 auto' }}>
      {/* Sección introductoria - explicación en español */}
      <section style={{ background: '#f7f9fc', padding: '20px', borderRadius: '8px', marginBottom: '18px' }}>
<h2 style={{ margin: 0 }}>Entendiendo el Análisis de Riesgos</h2>
<p style={{ marginTop: '10px', color: '#333' }}>
  Este motor de análisis de riesgos está diseñado para proporcionar una evaluación comprensible y detallada de las vulnerabilidades
  potenciales en su red. Utiliza una combinación de información técnica, como el Sistema de Puntuación de Vulnerabilidad Común (CVSS),
  la exposición del servicio y el contexto operativo para generar un puntaje de riesgo por hallazgo. Aquí se explica cómo se calcula:
</p>
        <ul>
<li><strong>Componente CVSS (60%):</strong> Utiliza la puntuación base CVSSv3, que varía de 0.0 a 10.0, escalada a un rango de 0 a 60. Esta puntuación refleja la gravedad de la vulnerabilidad.</li>
<li><strong>Componente de Exposición (30%):</strong> Evalúa si el puerto o servicio es público o comúnmente accesible desde el exterior, añadiendo hasta 30 puntos al puntaje total.</li>
<li><strong>Componente de Conteo (10%):</strong> Considera el número de vulnerabilidades en el mismo activo, añadiendo hasta 10 puntos adicionales si hay múltiples vulnerabilidades.</li>
        </ul>
<p style={{ marginTop: '8px' }}>
  El puntaje total se normaliza en una escala de 0 a 100 y se categoriza en las siguientes clasificaciones de riesgo:
</p>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <Badge label="Muy baja" color="#6c757d" />
          <Badge label="Baja" color="#28a745" />
          <Badge label="Media" color="#ffc107" />
          <Badge label="Alta" color="#fd7e14" />
          <Badge label="Muy alta" color="#dc3545" />
        </div>

        <h4 style={{ marginTop: '14px' }}>Tratamientos posibles</h4>
<p style={{ marginTop: '6px' }}>
  Dependiendo de la categoría de riesgo y el contexto específico, el motor sugiere uno de los siguientes tratamientos para mitigar el riesgo:
</p>
        <ul>
          <li><strong>Aceptar:</strong> Riesgo bajo. Registrar y monitorear, revisar en la próxima ventana de mantenimiento.</li>
          <li><strong>Mitigar:</strong> Aplicar parche/medidas compensatorias (firewall, segmentación, configuración segura).</li>
          <li><strong>Transferir:</strong> Si el servicio es de un proveedor/tercero, gestionar la responsabilidad contractual y controles compensatorios.</li>
          <li><strong>Evitar:</strong> Riesgo crítico/alta exposición — aislar o desconectar hasta aplicar corrección urgente.</li>
        </ul>

<p style={{ marginTop: '8px', fontStyle: 'italic' }}>
  Nota: Las recomendaciones proporcionadas incluyen pasos específicos sugeridos y una explicación personalizada basada en el hallazgo, que puede incluir detalles sobre el puerto, el producto y el CVE, si corresponde.
</p>
      </section>

      {/* Scan configuration and warning */}
      <div className="scan-config" style={{ marginBottom: '16px', padding: '16px', borderRadius: '8px', background: '#ffffff', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
        <h3 style={{ marginTop: 0 }}>Escáner de red</h3>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="text"
            id="target"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="e.g., 192.168.1.1, example.com"
            style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d7e0' }}
          />
          <button
            onClick={startScan}
            disabled={isScanning || !target.trim()}
            style={{
              padding: '8px 14px',
              borderRadius: 6,
              background: isScanning ? '#999' : '#0069d9',
              color: '#fff',
              border: 'none',
              cursor: isScanning ? 'default' : 'pointer'
            }}
          >
            {isScanning ? 'Escaneando... (puede tardar varios minutos)' : '🚀 Iniciar escaneo'}
          </button>
          <button
            onClick={exportCSV}
            disabled={!scanResults}
            style={{ padding: '8px 12px', borderRadius: 6, background: '#17a2b8', color: '#fff', border: 'none', cursor: 'pointer' }}
          >
            ⤓ Exportar CSV
          </button>
        </div>
        <p style={{ marginTop: 8, color: '#666' }}>
          Aviso: un escaneo puede tardar varios minutos dependiendo del objetivo y los scripts ejecutados. No interrumpir.
        </p>
      </div>

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
                            {vuln.severity?.toUpperCase() || 'UNKNOWN'}
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
                            <strong>Remediación sugerida (personalizada):</strong>
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
