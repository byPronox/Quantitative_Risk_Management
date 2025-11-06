import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { parseStringPromise } from 'xml2js';

/**
 * Nmap Scanner Service - Core scanning functionality (enhanced)
 * - Classifies assets by type (Infraestructura, Aplicaciones, Bases de datos)
 * - Enriches vulnerabilities using local NVD microservice (configurable URL)
 * - Computes a numeric risk score and maps it to categories:
 *   Muy baja, Baja, Media, Alta, Muy alta
 * - Attaches a recommended treatment per finding (aceptar, mitigar, transferir, evitar)
 * - Provides justification and remediation suggestions per finding
 *
 * Configuration via environment variables:
 * - NVD_SERVICE_URL (default: http://localhost:8000)
 */

/* Configuration */
const SCAN_TIMEOUT = 15 * 60 * 1000; // 15 minutes
const DEFAULT_TEMP_DIR = process.env.TEMP_DIR || (process.platform === 'win32' ? path.join(process.cwd(), 'temp') : '/app/temp');
const TEMP_DIR = DEFAULT_TEMP_DIR;
const NVD_SERVICE_URL = process.env.NVD_SERVICE_URL || 'http://localhost:8000';

/* Utilities: validation helpers */
export const validateIP = (ip) => {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipRegex.test(ip);
};

export const validateHostname = (hostname) => {
  const hostnameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/;
  return hostnameRegex.test(hostname);
};

const cleanupTempFile = (filePath) => {
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      console.log(`Cleaned up temporary file: ${filePath}`);
    }
  } catch (error) {
    console.warn(`Failed to cleanup file ${filePath}:`, error.message);
  }
};

/* --- New helpers for classification, enrichment, risk and treatment --- */

/**
 * Classify an asset given a service/port into one of:
 * - Infraestructura (e.g., web servers, load balancers)
 * - Aplicaciones (application-level services)
 * - Bases de datos (databases)
 */
const classifyAsset = (serviceName = '', port = '') => {
  const s = String(serviceName || '').toLowerCase();
  const p = String(port || '');

  // Common DB service identifiers
  const dbKeywords = ['mysql', 'mongodb', 'postgres', 'postgresql', 'mssql', 'sql', 'redis', 'oracle', 'cassandra'];
  for (const kw of dbKeywords) {
    if (s.includes(kw)) return 'Bases de datos';
  }
  // Common infra / web ports and names
  const infraPorts = ['80', '443', '8080', '8000', '8443', '3000', '9000'];
  const infraKeywords = ['http', 'https', 'nginx', 'apache', 'iis', 'lighttpd', 'haproxy', 'varnish'];
  if (infraPorts.includes(p) || infraKeywords.some(kw => s.includes(kw))) return 'Infraestructura';

  // SSH, FTP, SMTP are infrastructure as well
  const infraServiceKeywords = ['ssh', 'ftp', 'smtp', 'pop3', 'imap', 'telnet', 'rdp'];
  if (infraServiceKeywords.some(kw => s.includes(kw))) return 'Infraestructura';

  // Otherwise treat as application
  return 'Aplicaciones';
};

/**
 * Fetch NVD details for a CVE using configured NVD service.
 * Expects the NVD microservice to expose GET /vulnerabilities/{cve_id}
 * Returns null on failure or when not available.
 */
const fetchNvdForCve = async (cveId) => {
  if (!cveId) return null;
  const url = `${NVD_SERVICE_URL.replace(/\/$/, '')}/vulnerabilities/${encodeURIComponent(cveId)}`;
  try {
    // Use global fetch (Node 18+) - if not available, environment should provide a polyfill.
    const res = await fetch(url, { method: 'GET', headers: { 'Accept': 'application/json' } });
    if (!res.ok) {
      console.warn(`NVD service returned ${res.status} for ${cveId}`);
      return null;
    }
    const data = await res.json();
    return data;
  } catch (e) {
    console.warn(`Failed to fetch NVD data for ${cveId}:`, e.message);
    return null;
  }
};

/**
 * Compute a numeric risk score (0-100) for a given vulnerability context.
 * Formula (documented):
 *  - CVSS component (weight 70%): normalized CVSSv3 base score (0-10) scaled to 0-70
 *  - Exposure component (weight 20%): public/exposed port -> 20, otherwise 0
 *  - Count component (weight 10%): count of vulnerabilities for same asset normalized (min(count,5)/5 * 10)
 *
 * Total = cvss_component + exposure_component + count_component
 *
 * Rationale:
 *  - CVSS reflects inherent severity (most weight).
 *  - Exposure (public ports) amplifies risk.
 *  - Multiple issues on same asset slightly increase urgency.
 */
const computeRiskScore = (cvssBase = null, isExposed = false, vulnCountForAsset = 1) => {
  // New weights chosen for business logic balance:
  // - CVSS/base severity: 60%
  // - Exposure (public/exposed): 30%
  // - Multiple findings on same asset: 10%
  const cvss = (typeof cvssBase === 'number' && !isNaN(cvssBase)) ? Math.max(0, Math.min(10, cvssBase)) : 0;
  const compA = (cvss / 10) * 60; // 0-60
  const compB = isExposed ? 30 : 0; // 0 or 30
  const compC = (Math.min(vulnCountForAsset, 5) / 5) * 10; // 0-10
  let total = compA + compB + compC;
  // Safety caps
  if (total > 100) total = 100;
  if (total < 0) total = 0;
  // Round to one decimal for stable display
  return Math.round(total * 10) / 10;
};

/**
 * Map numeric score to category:
 * 0-10: Muy baja
 * 10.1-30: Baja
 * 30.1-60: Media
 * 60.1-85: Alta
 * 85.1-100: Muy alta
 */
const mapScoreToCategory = (score) => {
  if (score <= 10) return 'Muy baja';
  if (score <= 30) return 'Baja';
  if (score <= 60) return 'Media';
  if (score <= 85) return 'Alta';
  return 'Muy alta';
};

/**
 * Determine recommended treatment and provide personalized justification and remediation steps.
 * Treatments: aceptar, mitigar, transferir, evitar
 *
 * Heuristics:
 * - Very low risk -> aceptar (monitor)
 * - Low/Medium -> mitigar (patch, config, limit access)
 * - High -> mitigar (urgent) or transferir if asset is a third-party service (detected heuristically)
 * - Very high -> evitar (isolate, take offline if possible) + emergency patching
 */
const determineTreatment = (vuln, score, classification, nvdData) => {
  const category = mapScoreToCategory(score);
  const title = vuln.title || vuln.id || 'Vulnerability';
  const cve = vuln.cve || null;
  const product = vuln.context?.product || vuln.product || '';
  const reasonParts = [];
  const remediation = [];

  // Reason build
  reasonParts.push(`Hallazgo: "${title}".`);
  if (cve) reasonParts.push(`Referencia: ${cve}.`);
  reasonParts.push(`Tipo de activo: ${classification}.`);
  reasonParts.push(`Categoria de riesgo: ${category}. (Puntaje: ${score})`);
  if (vuln.output) {
    const excerpt = String(vuln.output).split('\n').slice(0, 2).join(' ').trim();
    if (excerpt) reasonParts.push(`Detalle: ${excerpt}`);
  }

  // NVD hints (patch availability, cvss, vendor statements)
  let patchHint = null;
  if (nvdData && typeof nvdData === 'object') {
    // Try to extract useful hints
    const descriptions = (nvdData.description && Array.isArray(nvdData.description) && nvdData.description.length > 0)
      ? (nvdData.description[0].value || '')
      : (nvdData.description?.value || '');
    if (descriptions && descriptions.toLowerCase().includes('no fix')) {
      patchHint = 'No hay parche disponible conocido';
    } else if (descriptions && (descriptions.toLowerCase().includes('fixed') || descriptions.toLowerCase().includes('patch'))) {
      patchHint = 'Parche o mitigación disponible según NVD';
    }
  }

  // Choose treatment
  let treatment = 'mitigar';
  if (score <= 30) treatment = 'aceptar';
  if (score > 30 && score <= 85) treatment = 'mitigar';
  if (score > 85) treatment = 'evitar';

  // If NVD indicates patch available and score is high, still mitigar (apply patch) rather than transfer
  if (classification === 'Bases de datos' && score > 70) {
    // Databases with high score -> prefer evitar (isolate) or mitigar depending on patch hint
    treatment = patchHint && patchHint.toLowerCase().includes('patch') ? 'mitigar' : 'evitar';
  }

  // Transferir scenario: if product looks like managed/third-party SaaS and score medium-high
  const productLower = String(product || '').toLowerCase();
  if ((productLower.includes('saas') || productLower.includes('managed service') || productLower.includes('hosted')) && score > 50) {
    treatment = 'transferir';
  }

  // Build remediation suggestions
  if (treatment === 'aceptar') {
    remediation.push('Monitoreo continuo del activo y revisión en la próxima ventana de mantenimiento.');
    remediation.push('Registrar el hallazgo en el sistema de gestión de vulnerabilidades para seguimiento.');
  } else if (treatment === 'mitigar') {
    remediation.push('Aplicar parche o actualización del proveedor lo antes posible.');
    remediation.push('Si el parche no está disponible, aplicar medidas compensatorias: limitar acceso por firewall, reglas SIG, o segmentación de red.');
    remediation.push('Revisar configuración y credenciales por seguridad (remover credenciales por defecto).');
  } else if (treatment === 'transferir') {
    remediation.push('Contactar al proveedor/tercero para solicitar parche o mitigación y SLA de resolución.');
    remediation.push('Formalizar la transferencia de riesgo mediante contrato o seguro si aplica.');
    remediation.push('Aplicar controles compensatorios en la red para reducir exposición mientras proveedor actúa.');
  } else if (treatment === 'evitar') {
    remediation.push('Aislar inmediatamente el activo de la red de producción (segmentación/quarantine).');
    remediation.push('Aplicar parche de emergencia o revertir servicio si el parche no está disponible.');
    remediation.push('Considerar restaurar desde snapshot conocido seguro o desplegar instancia reemplazo parcheada.');
  }

  // Augment remediation with specific hints from NVD where possible
  if (patchHint) remediation.unshift(`NVD: ${patchHint}.`);

  const reason = reasonParts.join(' ');
  return { treatment, reason, remediation };
};

/* --- Existing XML processing logic (slightly adapted to integrate enrichment) --- */

const extractScriptOutput = (script) => {
  if (script && script.$ && typeof script.$.output === 'string' && script.$.output.trim() !== '') {
    return script.$.output.trim();
  }
  if (script && script.output && Array.isArray(script.output)) {
    try {
      return script.output.map(o => (typeof o === 'string' ? o : JSON.stringify(o))).join('\n').trim();
    } catch (e) {
      return String(script.output);
    }
  }
  if (script && script.table) {
    try {
      return JSON.stringify(script.table);
    } catch (e) {
      return String(script.table);
    }
  }
  try {
    return JSON.stringify(script);
  } catch (e) {
    return '';
  }
};

const normalizeScript = (script, context = {}) => {
  const id = script && script.$ && script.$.id ? script.$.id : 'unknown';

  // Force rawOutput to string to avoid boolean/false values showing as false
  let rawOutput = extractScriptOutput(script);
  if (rawOutput === null || typeof rawOutput === 'undefined') rawOutput = '';
  // Convert to string but treat literal boolean strings and solitary 'false'/'true' as empty (these come from some nmap script outputs)
  rawOutput = String(rawOutput);
  if (rawOutput.trim().toLowerCase() === 'false' || rawOutput.trim().toLowerCase() === 'true') rawOutput = '';
  rawOutput = rawOutput.trim();

  let severity = 'Unknown';
  let title = id || 'Unknown Vulnerability';
  let description = rawOutput || '';
  let cve = null;

  const lowerId = String(id).toLowerCase();
  const lowerOutput = String(rawOutput).toLowerCase();

  if (lowerId.includes('slowloris') || lowerOutput.includes('slowloris')) {
    severity = 'High';
    title = 'Slowloris DOS attack';
    description = description || 'Slowloris keeps many connections to the target web server open, potentially causing denial of service.';
  }
  if (lowerOutput.includes('vulnerable') && severity === 'Unknown') {
    severity = 'Medium';
  }

  const cveMatch = description.match(/CVE-\d{4}-\d{4,7}/i);
  if (cveMatch && cveMatch.length > 0) {
    cve = cveMatch[0].toUpperCase();
  } else {
    // Try to extract CVE-like identifiers from other places (id, title)
    try {
      const idCve = String(id || '').match(/CVE-\d{4}-\d{4,7}/i);
      if (idCve && idCve.length > 0) cve = idCve[0].toUpperCase();
    } catch (e) {}
    if (!cve) {
      const titleCve = String(title || '').match(/CVE-\d{4}-\d{4,7}/i);
      if (titleCve && titleCve.length > 0) cve = titleCve[0].toUpperCase();
    }

    // Some scripts encode CVE/ids in different forms, try looser matches (e.g. CVE-YYYY-NNNN with variable digits)
    if (!cve) {
      const loose = description.match(/CVE[-\s:]?\s*\d{4}[-\s]?\d{4,7}/i);
      if (loose && loose.length > 0) cve = loose[0].toUpperCase().replace(/\s+/g, '').replace(/[:]/g,'-');
    }

    // Fallback: capture vendor bulletin identifiers (e.g. ms10-054) as a reference if no CVE found
    if (!cve) {
      const msMatch = (String(id || '') + ' ' + String(description || '')).match(/ms\d{2}-\d{3}/i);
      if (msMatch && msMatch.length > 0) {
        // store as a reference in the cve field using lowercase to indicate non-CVE
        cve = msMatch[0].toLowerCase();
      }
    }
  }

  // If the description is empty, try to build a friendly title from the id
  if ((!description || description.length === 0) && id && id !== 'unknown') {
    // replace common separators with spaces and trim
    const friendly = String(id).replace(/[-_]/g, ' ').replace(/\s+/g, ' ').trim();
    title = friendly.length > 0 ? friendly : title;
  } else if ((title === id || title.toLowerCase().includes('unknown')) && description) {
    const firstLine = description.split('\n').find(l => l.trim().length > 0);
    if (firstLine && firstLine.length < 120) {
      title = firstLine.trim().slice(0, 120);
    }
  }

  // Build normalized object
  return {
    id,
    severity,
    title,
    description,
    cve,
    output: rawOutput,
    table: script.table || null,
    context: {
      type: context.type || 'host',
      port: context.port || null,
      product: context.product || null
    }
  };
};

/**
 * Decide whether a normalized vulnerability should be ignored from the results.
 * Ignore common "no findings" outputs to avoid cluttering results with negative checks.
 */
const shouldIgnoreVuln = (vuln) => {
  if (!vuln) return true;
  const out = String(vuln.output || '').toLowerCase().trim();
  const title = String(vuln.title || '').toLowerCase();
  const desc = String(vuln.description || '').toLowerCase();

  // Ignore empty outputs
  if (!out && (!title || title.length === 0) && (!desc || desc.length === 0)) return true;

  // Common messages indicating no findings
  const noFindingsPatterns = [
    "couldn't find any",
    "could not find any",
    "no vulnerabilities",
    "no issues found",
    "no reply from server (timeout)",
    "no reply from server",
    "couldn't find any csrf",
    "couldn't find any stored",
    "couldn't find any dom based",
    "couldn't find any dom",
    "couldn't find any xss",
    "could not negotiate",
    "failed to receive bytes",
    "failed to receive bytes: eof",
    "no findings",
    "unable to connect",
    "connection refused",
    "connection reset",
    "timeout",
    "not vulnerable",
    "not exploitable",
    "service detection performed",
    "tcpwrapped",
    // Additional patterns observed in practice
    "couldn't connect",
    "no banner",
    "banner not available",
    "service unrecognized",
    "error",
    "exception",
    "not accessible",
    "refused",
    "reset by peer",
    "closed",
    "no response",
    "filtering (firewall)",
    "filtered",
    "unreachable"
  ];

  for (const p of noFindingsPatterns) {
    if (out.includes(p) || title.includes(p) || desc.includes(p)) return true;
  }

  // If the output is a short cryptic 'false' or similar, ignore it
  if (out === 'false' || out === 'true') return true;

  return false;
};

/* processXMLOutput: parse xml and then enrich results with classification, NVD, risk and treatment */
const processXMLOutput = async (xmlFilePath, target) => {
  try {
    console.log(`Processing XML file: ${xmlFilePath}`);
    const xmlContent = fs.readFileSync(xmlFilePath, 'utf8');
    const result = await parseStringPromise(xmlContent);

    const nmaprun = result.nmaprun;
    if (!nmaprun || !nmaprun.host || !nmaprun.host[0]) {
      return {
        ip: target,
        os: 'Unknown',
        status: 'down',
        services: [],
        vulnerabilities: [],
        timestamp: new Date().toISOString(),
        scanDuration: nmaprun?.$?.scanner || 'unknown',
        message: 'Host seems down or unreachable. No data found.'
      };
    }

    const host = nmaprun.host[0];
    const hostStatus = host.status?.[0]?.$?.state || 'unknown';
    let os = 'Unknown';
    if (host.os && host.os[0] && host.os[0].osmatch && host.os[0].osmatch[0]) {
      os = host.os[0].osmatch[0].$.name || 'Unknown';
    }

    const services = [];
    const portsList = [];
    // Build map port->product so we can pass product reliably to script normalizer
    const portProductMap = {};
    if (host.ports && host.ports[0] && host.ports[0].port) {
      const ports = host.ports[0].port;
      ports.forEach((port) => {
        try {
          const portData = port.$ || {};
          const serviceData = port.service?.[0]?.$ || {};
          const service = {
            port: portData.portid || 'unknown',
            protocol: portData.protocol || 'tcp',
            state: (port.state && port.state[0] && port.state[0].$.state) ? port.state[0].$.state : (portData.state || 'unknown'),
            name: serviceData.name || 'unknown',
            product: serviceData.product || '',
            version: serviceData.version || '',
            method: serviceData.method || 'unknown',
            conf: serviceData.conf || '0',
            extrainfo: serviceData.extrainfo || ''
          };
          services.push(service);

          // Populate map for reliable product lookup later
          if (service.port) {
            portProductMap[String(service.port)] = service.product || '';
          }

          const portEntry = {
            port: service.port,
            state: service.state,
            service: service.name,
            protocol: service.protocol,
            product: service.product,
            version: service.version
          };
          portsList.push(portEntry);
        } catch (portError) {
          console.warn('Error processing port:', portError.message);
        }
      });
    }

    // Extract vulnerabilities (hostscript + port scripts)
    const vulnerabilities = [];
    if (host.hostscript && host.hostscript[0] && host.hostscript[0].script) {
      const scripts = host.hostscript[0].script;
      scripts.forEach(script => {
        try {
          const vuln = normalizeScript(script, { type: 'host' });
          if (!shouldIgnoreVuln(vuln)) vulnerabilities.push(vuln);
        } catch (e) {
          console.warn('Failed to normalize host script:', e.message);
        }
      });
    }

    if (host.ports && host.ports[0] && host.ports[0].port) {
      const ports = host.ports[0].port;
      ports.forEach(port => {
        const portAttr = port && port.$ ? port.$ : {};
        const portId = portAttr.portid || null;
        const portScripts = [];
        if (port.script && Array.isArray(port.script)) {
          port.script.forEach(s => portScripts.push(s));
        }
        if (port.scripts && Array.isArray(port.scripts)) {
          port.scripts.forEach(s => portScripts.push(s));
        }
        if (port.script && port.script[0] && port.script[0].script && Array.isArray(port.script[0].script)) {
          port.script[0].script.forEach(s => portScripts.push(s));
        }

        if (Array.isArray(portScripts) && portScripts.length > 0) {
          portScripts.forEach(scriptNode => {
            try {
              // Pass product from portProductMap to ensure product is available
              const product = portProductMap[String(portId)] || '';
              const vuln = normalizeScript(scriptNode, { type: 'port', port: portId, product });
              if (!shouldIgnoreVuln(vuln)) vulnerabilities.push(vuln);
            } catch (e) {
              console.warn(`Failed to normalize script for port ${portId}:`, e.message);
            }
          });
        }
      });
    }

    // Enrichment: classify assets and compute per-vuln risk/treatment
    // Build a map of assetKey -> vulnCount for normalization
    const assetVulnCount = {};
    for (const v of vulnerabilities) {
      const key = `${v.context?.type || 'host'}:${v.context?.port || 'host'}`;
      assetVulnCount[key] = (assetVulnCount[key] || 0) + 1;
    }

    // Enhance each vulnerability
    const enhancedVulns = [];
    for (const v of vulnerabilities) {
      try {
        // Ensure baseline types
        v.output = String(v.output || '');
        v.title = v.title || v.id || 'Unknown Vulnerability';
        v.description = v.description || v.output || '';

        // Classify asset
        const classification = classifyAsset(v.context?.product || v.title || v.context?.type, v.context?.port);
        const assetKey = `${v.context?.type || 'host'}:${v.context?.port || 'host'}`;
        const vulnCountForAsset = assetVulnCount[assetKey] || 1;

        // Attempt to get CVE details from NVD if CVE present
        let nvdData = null;
        if (v.cve) {
          nvdData = await fetchNvdForCve(v.cve);
        }

        // Extract CVSS base score if available in NVD response
        let cvssBase = null;
        if (nvdData && nvdData.metrics) {
          // Different NVD responses may have different shapes; attempt common fields
          try {
            // Attempt v3 metric first
            const metricV3 = nvdData.metrics && nvdData.metrics.cvssMetricV31;
            if (metricV3 && Array.isArray(metricV3) && metricV3.length > 0 && metricV3[0].cvssData) {
              cvssBase = Number(metricV3[0].cvssData.baseScore || metricV3[0].cvssData['baseScore']);
            } else if (nvdData.cvss && nvdData.cvss.baseScore) {
              cvssBase = Number(nvdData.cvss.baseScore);
            } else if (nvdData.impact && nvdData.impact.baseMetricV3 && nvdData.impact.baseMetricV3.cvssV3 && nvdData.impact.baseMetricV3.cvssV3.baseScore) {
              cvssBase = Number(nvdData.impact.baseMetricV3.cvssV3.baseScore);
            }
          } catch (e) {
            // ignore
          }
        }

        // Fallback: try to infer severity from normalized severity or textual 'severity' field
        if (cvssBase === null) {
          const sev = (v.severity || '').toLowerCase();
          if (sev === 'high') cvssBase = 8.5;
          else if (sev === 'medium') cvssBase = 5.5;
          else if (sev === 'low') cvssBase = 2.5;
          else cvssBase = 3.0; // conservative default
        }

        // Determine exposure: is this port commonly public-facing?
        const exposedPorts = ['80','443','8080','8443','21','22','23','25','3306','5432','27017','3389'];
        const isExposed = !!(v.context && v.context.port && exposedPorts.includes(String(v.context.port)));

        const score = computeRiskScore(cvssBase, isExposed, vulnCountForAsset);
        const category = mapScoreToCategory(score);
        const treatmentInfo = determineTreatment(v, score, classification, nvdData);

        // Ensure we always include risk and treatment objects (avoid empty values in output)
        enhancedVulns.push({
          ...v,
          classification,
          cvssBase,
          nvd: nvdData || null,
          risk: {
            score: (typeof score === 'number') ? score : 0,
            category: category || 'Muy baja'
          },
          treatment: {
            treatment: treatmentInfo?.treatment || 'aceptar',
            reason: treatmentInfo?.reason || 'Revisión manual recomendada.',
            remediation: Array.isArray(treatmentInfo?.remediation) ? treatmentInfo.remediation : (treatmentInfo?.remediation ? [treatmentInfo.remediation] : ['Revisar manualmente.'])
          }
        });
      } catch (e) {
        console.warn('Failed to enrich vulnerability:', e.message);
        enhancedVulns.push({
          ...v,
          classification: 'Unknown',
          risk: { score: 0, category: 'Muy baja' },
          treatment: { treatment: 'aceptar', reason: 'Error al enriquecer; conservar y revisar manualmente.', remediation: ['Revisar manualmente.'] }
        });
      }
    }

    // Aggregate high-level risk summary for the scan (max score, average)
    const scores = enhancedVulns.map(v => (v.risk && typeof v.risk.score === 'number') ? v.risk.score : 0);
    const maxScore = scores.length > 0 ? Math.max(...scores) : 0;
    const avgScore = scores.length > 0 ? Math.round((scores.reduce((a,b) => a+b,0)/scores.length)*10)/10 : 0;
    const aggregateCategory = mapScoreToCategory(maxScore);

    const scanResult = {
      ip: target,
      host: target,
      os: os,
      status: hostStatus,
      ports: portsList,
      services: services,
      vulnerabilities: enhancedVulns,
      summary: {
        total_vulnerabilities: enhancedVulns.length,
        max_score: maxScore,
        average_score: avgScore,
        aggregate_category: aggregateCategory,
        timestamp: new Date().toISOString()
      },
      timestamp: new Date().toISOString(),
      scanDuration: nmaprun.$.scanner ? nmaprun.$.scanner : 'unknown'
    };

    console.log(`Scan result processed successfully for ${target}`);
    return scanResult;

  } catch (error) {
    console.error('XML processing failed:', error);
    throw new Error(`XML processing failed: ${error.message}`);
  }
};

/* --- Main scanning and helper functions (unchanged entrypoints) --- */

export const scanIP = (target) => {
  return new Promise((resolve, reject) => {
    console.log(`Starting nmap scan for target: ${target}`);

    if (!target) {
      reject({ error: 'Missing target parameter', details: 'Target IP or hostname is required' });
      return;
    }

    if (!validateIP(target) && !validateHostname(target)) {
      reject({ error: 'Invalid target format', details: 'Target must be a valid IP address or hostname' });
      return;
    }

    try {
      fs.mkdirSync(TEMP_DIR, { recursive: true });
    } catch (e) {
      console.warn(`Could not create TEMP_DIR ${TEMP_DIR}:`, e.message);
    }

    const timestamp = Date.now();
    const xmlFilePath = path.resolve(TEMP_DIR, `scan_result_${timestamp}.xml`);
    const quotedXml = `"${xmlFilePath}"`;
    const nmapCommand = `nmap -Pn -sV --script vuln --script-timeout=120s --max-retries=5 ${target} -oX ${quotedXml}`;
    console.log(`Executing vulnerability scan command: ${nmapCommand}`);

    const childProcess = exec(nmapCommand, {
      timeout: SCAN_TIMEOUT,
      maxBuffer: 1024 * 1024 * 10
    }, async (error, stdout, stderr) => {
      console.log('Nmap execution completed');
      console.log('STDOUT length:', (stdout || '').length);
      console.log('STDERR length:', (stderr || '').length);

      if (error) {
        console.error('Nmap execution failed:', error);
        cleanupTempFile(xmlFilePath);
        reject({
          error: 'Nmap execution failed',
          details: stderr || error.message,
          code: error.code,
          signal: error.signal
        });
        return;
      }

      try {
        if (!fs.existsSync(xmlFilePath)) {
          throw new Error('XML output file was not created');
        }

        const scanResult = await processXMLOutput(xmlFilePath, target);
        cleanupTempFile(xmlFilePath);
        resolve(scanResult);

      } catch (processingError) {
        console.error('Error processing scan results:', processingError);
        cleanupTempFile(xmlFilePath);
        reject({
          error: 'XML processing failed',
          details: processingError.message
        });
      }
    });

    childProcess.on('error', (error) => {
      console.error('Child process error:', error);
      cleanupTempFile(xmlFilePath);
      reject({
        error: 'Process execution failed',
        details: error.message
      });
    });

    childProcess.on('exit', (code, signal) => {
      console.log(`Nmap process exited with code: ${code}, signal: ${signal}`);
    });
  });
};

export const testNmapInstallation = () => {
  return new Promise((resolve, reject) => {
    exec('nmap --version', (error, stdout, stderr) => {
      if (error) {
        reject({
          error: 'Nmap not found',
          details: 'Nmap is not installed or not in PATH',
          stderr: stderr
        });
        return;
      }
      resolve({
        installed: true,
        version: stdout.trim(),
        message: 'Nmap is properly installed'
      });
    });
  });
};

export const getAvailableScripts = () => {
  return new Promise((resolve, reject) => {
    exec('nmap --script-help vuln', (error, stdout, stderr) => {
      if (error) {
        reject({
          error: 'Failed to get scripts',
          details: stderr || error.message
        });
        return;
      }
      resolve({
        scripts: stdout.trim(),
        message: 'Vulnerability scripts available'
      });
    });
  });
};
