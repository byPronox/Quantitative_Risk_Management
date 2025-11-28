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
      {/* Sección de Documentación Integral */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginBottom: '32px' }}>

        {/* 1. Guía Básica (Analogía) */}
        <section style={{ background: '#fff', padding: '24px', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', borderLeft: '6px solid #3182ce' }}>
          <h2 style={{ margin: '0 0 16px 0', color: '#2c5282', fontSize: '1.6rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            📘 Guía Básica: Entendiendo el Escaneo
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            <div>
              <h3 style={{ color: '#2b6cb0', marginTop: 0 }}>🏠 La Analogía de la "Casa Digital"</h3>
              <p style={{ lineHeight: '1.6', color: '#4a5568' }}>
                Imagine que su red es su <strong>casa</strong>.
                <br /><br />
                🚪 <strong>Puertos = Puertas y Ventanas:</strong> Son las entradas a su casa. Algunas deben estar abiertas (como la puerta principal para visitas), pero otras no (la ventana del baño).
                <br />
                🔓 <strong>Vulnerabilidades = Cerraduras Rotas:</strong> Son fallos que permitirían a un ladrón entrar, incluso si la puerta está cerrada.
                <br />
                🕵️ <strong>El Escáner = Inspector de Seguridad:</strong> Esta herramienta revisa cada puerta y ventana para ver si están abiertas o si tienen cerraduras defectuosas.
              </p>
            </div>
            <div style={{ background: '#ebf8ff', padding: '16px', borderRadius: '8px' }}>
              <h3 style={{ color: '#2c5282', marginTop: 0 }}>🚦 ¿Cómo leo los resultados?</h3>
              <ul style={{ paddingLeft: '20px', lineHeight: '1.8', color: '#2d3748' }}>
                <li>🟢 <strong>Verde (Seguro):</strong> Puertas cerradas o con buenas cerraduras. No hay peligro inmediato.</li>
                <li>🟡 <strong>Amarillo (Precaución):</strong> Una ventana abierta que no debería, o una cerradura vieja. Requiere atención.</li>
                <li>🔴 <strong>Rojo (Peligro):</strong> La puerta principal está abierta de par en par y sin llave. <strong>Acción inmediata requerida.</strong></li>
              </ul>
            </div>
          </div>
        </section>

        {/* 2. Diccionario de Términos */}
        <section style={{ background: '#fff', padding: '24px', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <h2 style={{ margin: '0 0 20px 0', color: '#2d3748', fontSize: '1.4rem' }}>📖 Diccionario para No Expertos</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
            <div style={{ border: '1px solid #e2e8f0', padding: '16px', borderRadius: '8px' }}>
              <strong style={{ color: '#e53e3e', fontSize: '1.1em' }}>Vulnerabilidad</strong>
              <p style={{ fontSize: '0.95em', color: '#718096', marginTop: '8px' }}>
                Un error de fábrica en el software. Es como comprar una caja fuerte que tiene un defecto: si golpeas la esquina, se abre sola.
              </p>
            </div>
            <div style={{ border: '1px solid #e2e8f0', padding: '16px', borderRadius: '8px' }}>
              <strong style={{ color: '#d69e2e', fontSize: '1.1em' }}>CVSS (Puntuación Base)</strong>
              <p style={{ fontSize: '0.95em', color: '#718096', marginTop: '8px' }}>
                Una nota del 0 al 10 que dice qué tan peligrosa es la falla <em>por sí sola</em>.
                <br /><strong>10 = Huracán Cat. 5</strong> (Destrucción total).
                <br /><strong>1 = Lluvia ligera</strong> (Molesto pero no grave).
              </p>
            </div>
            <div style={{ border: '1px solid #e2e8f0', padding: '16px', borderRadius: '8px' }}>
              <strong style={{ color: '#3182ce', fontSize: '1.1em' }}>Exposición</strong>
              <p style={{ fontSize: '0.95em', color: '#718096', marginTop: '8px' }}>
                ¿Dónde está el problema?
                <br /><strong>Pública:</strong> En la acera (Cualquiera lo ve).
                <br /><strong>Interna:</strong> Dentro de la casa (Solo invitados lo ven).
              </p>
            </div>
          </div>
        </section>

        {/* 3. El Modelo de Riesgo (Profundo) */}
        <section style={{ background: '#2d3748', color: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
          <h2 style={{ margin: '0 0 24px 0', color: '#fff', fontSize: '1.5rem', borderBottom: '1px solid #4a5568', paddingBottom: '12px' }}>
            🔬 El Modelo de Riesgo: ¿Por qué calculamos así?
          </h2>

          <div style={{ background: 'rgba(255,255,255,0.1)', padding: '16px', borderRadius: '8px', marginBottom: '24px', textAlign: 'center' }}>
            <span style={{ fontSize: '1.2em', fontFamily: 'monospace' }}>Riesgo = Impacto (Daño) × Probabilidad (Facilidad)</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            {/* Impacto */}
            <div>
              <h3 style={{ color: '#fc8181', display: 'flex', alignItems: 'center', gap: '8px' }}>
                💣 Impacto (60%) - "El Tamaño de la Bomba"
              </h3>
              <p style={{ lineHeight: '1.6', color: '#cbd5e0' }}>
                <strong>¿Qué es?</strong> Usamos el CVSS Base.
                <br />
                <strong>El "Por Qué" Real:</strong> Imaginemos dos explosivos: un petardo y dinamita.
                La dinamita (CVSS alto) <em>siempre</em> será más peligrosa por su naturaleza, sin importar dónde esté.
                Por eso tiene el peso más alto (60%), porque define el <strong>techo</strong> del daño posible.
                Si el impacto es bajo, el riesgo nunca puede ser crítico, no importa qué tan expuesto esté.
              </p>
            </div>

            {/* Probabilidad */}
            <div>
              <h3 style={{ color: '#63b3ed', display: 'flex', alignItems: 'center', gap: '8px' }}>
                🎲 Probabilidad (40%) - "La Ubicación"
              </h3>
              <div style={{ marginBottom: '16px' }}>
                <strong style={{ color: '#90cdf4' }}>1. Exposición (30%)</strong>
                <p style={{ lineHeight: '1.6', color: '#cbd5e0', fontSize: '0.95em' }}>
                  Una dinamita en una caja fuerte en el sótano (Puerto Cerrado) es menos riesgosa que un petardo en la calle (Puerto Abierto).
                  La accesibilidad es el factor #1 que convierte una "amenaza teórica" en un "ataque real".
                </p>
              </div>
              <div>
                <strong style={{ color: '#90cdf4' }}>2. Densidad (10%) - "Ventanas Rotas"</strong>
                <p style={{ lineHeight: '1.6', color: '#cbd5e0', fontSize: '0.95em' }}>
                  Si ves una casa con una ventana rota, es probable que tenga más problemas.
                  Un servidor con 10 fallos indica descuido, aumentando la probabilidad de que un atacante encuentre <em>alguna</em> forma de entrar.
                </p>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid #4a5568' }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#a0aec0' }}>¿Por qué esta fórmula y no otra?</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '0.9em' }}>
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px' }}>
                <strong>vs. Solo CVSS</strong>
                <p style={{ color: '#cbd5e0', margin: '4px 0 0 0' }}>CVSS solo no ve el contexto. Un fallo crítico en un servidor desconectado no es un riesgo real. Nosotros corregimos eso.</p>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px' }}>
                <strong>vs. Probabilístico Puro</strong>
                <p style={{ color: '#cbd5e0', margin: '4px 0 0 0' }}>Requiere datos históricos de años que no tenemos. Nuestro modelo es más práctico y directo.</p>
              </div>
              <div style={{ background: 'rgba(49, 151, 149, 0.2)', border: '1px solid #319795', padding: '12px', borderRadius: '6px' }}>
                <strong>Nuestra Elección</strong>
                <p style={{ color: '#81e6d9', margin: '4px 0 0 0' }}>Modelo <strong>Determinista</strong>: Transparente, calculable y sin "magia negra". Usted puede verificar el número.</p>
              </div>
            </div>
          </div>
        </section>

        {/* 4. Guía Paso a Paso */}
        <section style={{ background: '#fff', padding: '24px', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <h2 style={{ margin: '0 0 20px 0', color: '#2d3748', fontSize: '1.4rem' }}>🚀 Guía de Uso Paso a Paso</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
              <div style={{ background: '#3182ce', color: 'white', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>1</div>
              <div>
                <strong style={{ fontSize: '1.1em', color: '#2d3748' }}>Ingrese el Objetivo (Input)</strong>
                <p style={{ color: '#4a5568', margin: '4px 0' }}>
                  Escriba la <strong>Dirección IP</strong> (ej. <code>192.168.1.1</code>) o Dominio.
                  <br /><em>Analogía:</em> Es como darle al inspector la dirección de la casa que debe revisar.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
              <div style={{ background: '#3182ce', color: 'white', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>2</div>
              <div>
                <strong style={{ fontSize: '1.1em', color: '#2d3748' }}>Analice los Resultados</strong>
                <p style={{ color: '#4a5568', margin: '4px 0' }}>
                  Verá una lista de "Puertos Abiertos" y "Vulnerabilidades".
                  <br /><strong>Puertos:</strong> ¿Qué puertas están abiertas? (Web, Correo, Base de Datos).
                  <br /><strong>OS:</strong> ¿Qué sistema operativo usa? (El "acento" del servidor).
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
              <div style={{ background: '#3182ce', color: 'white', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>3</div>
              <div>
                <strong style={{ fontSize: '1.1em', color: '#2d3748' }}>Tome Acción (Remediación)</strong>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginTop: '8px' }}>
                  <div style={{ background: '#f0fff4', padding: '8px', borderRadius: '4px', border: '1px solid #c6f6d5' }}>
                    <strong style={{ color: '#2f855a' }}>🛡️ Mitigar</strong>
                    <div style={{ fontSize: '0.9em' }}>Arreglarlo (Parchear o cerrar puerto).</div>
                  </div>
                  <div style={{ background: '#fffaf0', padding: '8px', borderRadius: '4px', border: '1px solid #fbd38d' }}>
                    <strong style={{ color: '#c05621' }}>📝 Aceptar</strong>
                    <div style={{ fontSize: '0.9em' }}>El riesgo es bajo, lo dejamos así por ahora.</div>
                  </div>
                  <div style={{ background: '#ebf8ff', padding: '8px', borderRadius: '4px', border: '1px solid #bee3f8' }}>
                    <strong style={{ color: '#2b6cb0' }}>👉 Transferir</strong>
                    <div style={{ fontSize: '0.9em' }}>Es culpa del proveedor (ej. AWS), que ellos lo arreglen.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Scan configuration and warning */}
      <div className="scan-config" style={{ marginBottom: '16px', padding: '16px', borderRadius: '8px', background: '#ffffff', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
        <h3 style={{ marginTop: 0 }}>Escáner de red</h3>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="text"
            id="target"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="ej: 192.168.1.1, ejemplo.com"
            style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d7e0' }}
            aria-label="IP o dominio objetivo"
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
            aria-label="Iniciar escaneo de red"
          >
            {isScanning ? 'Escaneando... (puede tardar varios minutos)' : '🚀 Iniciar escaneo'}
          </button>
          <button
            onClick={exportCSV}
            disabled={!scanResults}
            style={{ padding: '8px 12px', borderRadius: 6, background: '#17a2b8', color: '#fff', border: 'none', cursor: 'pointer' }}
            aria-label="Exportar resultados del escaneo a CSV"
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

                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>                        <div style={{ color: '#333' }}>
                        <strong>Descripción:</strong>
                        <div style={{ marginTop: 6, whiteSpace: 'pre-wrap', color: '#444' }}>
                          {vuln.description || 'No hay descripción detallada disponible.'}
                        </div>
                      </div>

                        {/* Treatment and personalized remediation */}                        <div style={{ marginTop: 6, background: '#fbfcfe', padding: 10, borderRadius: 6 }}>
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
