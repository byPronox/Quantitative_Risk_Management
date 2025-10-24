import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { parseStringPromise } from 'xml2js';

/**
 * Nmap Scanner Service - Core scanning functionality
 * Implements exact nmap command: nmap -sV --script vuln [IP] -oX scan_result.xml
 */

// Configuration
const SCAN_TIMEOUT = 15 * 60 * 1000; // 15 minutos timeout
const TEMP_DIR = '/app/temp';

/**
 * Validates IP address format
 * @param {string} ip - IP address to validate
 * @returns {boolean} - True if valid IP format
 */
export const validateIP = (ip) => {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipRegex.test(ip);
};

/**
 * Validates hostname format
 * @param {string} hostname - Hostname to validate
 * @returns {boolean} - True if valid hostname format
 */
export const validateHostname = (hostname) => {
  const hostnameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/;
  return hostnameRegex.test(hostname);
};

/**
 * Cleans up temporary XML files
 * @param {string} filePath - Path to file to delete
 */
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

/**
 * Processes nmap XML output and extracts structured data
 * @param {string} xmlFilePath - Path to XML file
 * @param {string} target - Target IP or hostname
 * @returns {Object} - Structured scan result
 */
const processXMLOutput = async (xmlFilePath, target) => {
  try {
    console.log(`Processing XML file: ${xmlFilePath}`);
    
    // Read XML file
    const xmlContent = fs.readFileSync(xmlFilePath, 'utf8');
    console.log(`XML file size: ${xmlContent.length} characters`);
    
    // Parse XML
    const result = await parseStringPromise(xmlContent);
    console.log('XML parsed successfully');
    
    // Extract host data
    const nmaprun = result.nmaprun;
    // If no host data, return a valid empty scan result instead of error
    if (!nmaprun || !nmaprun.host || !nmaprun.host[0]) {
      console.warn('No host data found in XML, returning empty scan result');
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
    console.log('Host data extracted from XML');
    
    // Extract host status
    const hostStatus = host.status?.[0]?.$?.state || 'unknown';
    console.log(`Host status: ${hostStatus}`);
    
    // Extract OS information
    let os = 'Unknown';
    if (host.os && host.os[0] && host.os[0].osmatch && host.os[0].osmatch[0]) {
      os = host.os[0].osmatch[0].$.name || 'Unknown';
    }
    console.log(`Detected OS: ${os}`);
    
    // Extract ports and services
    const services = [];
    if (host.ports && host.ports[0] && host.ports[0].port) {
      const ports = host.ports[0].port;
      console.log(`Found ${ports.length} ports`);
      
      ports.forEach((port, index) => {
        try {
          const portData = port.$;
          const serviceData = port.service?.[0]?.$ || {};
          
          const service = {
            port: portData.portid || 'unknown',
            protocol: portData.protocol || 'tcp',
            state: portData.state || 'unknown',
            name: serviceData.name || 'unknown',
            product: serviceData.product || '',
            version: serviceData.version || '',
            method: serviceData.method || 'unknown',
            conf: serviceData.conf || '0',
            extrainfo: serviceData.extrainfo || ''
          };
          
          services.push(service);
          console.log(`Port ${index + 1}: ${service.port}/${service.protocol} - ${service.name} (${service.product} ${service.version})`);
        } catch (portError) {
          console.warn(`Error processing port ${index}:`, portError.message);
        }
      });
    }
    
    // Extract vulnerability scripts if present
    const vulnerabilities = [];
    if (host.hostscript && host.hostscript[0] && host.hostscript[0].script) {
      const scripts = host.hostscript[0].script;
      scripts.forEach(script => {
        // Mapeo mejorado para los scripts más comunes
        let severity = 'Unknown';
        let title = script.$.id || 'Unknown Vulnerability';
        let description = script.$.output || '';
        let cve = null;
        // Ejemplo: Slowloris
        if (title.toLowerCase().includes('slowloris')) {
          severity = 'High';
          title = 'Slowloris DOS attack';
          description = script.$.output || 'Slowloris tries to keep many connections to the target web server open and hold them open as long as possible.';
          // Buscar CVE en el output
          const cveMatch = description.match(/CVE-\d{4}-\d{4,7}/);
          if (cveMatch) cve = cveMatch[0];
        }
        // Buscar CVE genérico en el output
        if (!cve) {
          const cveMatch = description.match(/CVE-\d{4}-\d{4,7}/);
          if (cveMatch) cve = cveMatch[0];
        }
        vulnerabilities.push({
          id: script.$.id || 'unknown',
          severity,
          title,
          description,
          cve,
          output: script.$.output || '',
          table: script.table || null
        });
      });
    }
    
    const scanResult = {
      ip: target,
      os: os,
      status: hostStatus,
      services: services,
      vulnerabilities: vulnerabilities,
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

/**
 * Main scanning function - executes nmap with exact command specified
 * @param {string} target - IP address or hostname to scan
 * @returns {Promise<Object>} - Structured scan result
 */
export const scanIP = (target) => {
  return new Promise((resolve, reject) => {
    console.log(`Starting nmap scan for target: ${target}`);
    
    // Validate target
    if (!target) {
      reject({ error: 'Missing target parameter', details: 'Target IP or hostname is required' });
      return;
    }
    
    if (!validateIP(target) && !validateHostname(target)) {
      reject({ error: 'Invalid target format', details: 'Target must be a valid IP address or hostname' });
      return;
    }
    
    // Generate unique filename for this scan
    const timestamp = Date.now();
    const xmlFilePath = path.join(TEMP_DIR, `scan_result_${timestamp}.xml`);
    
    // Simplified nmap command for vulnerability scanning
    // Always use -Pn to skip ping and scan even if host does not reply
    const nmapCommand = `nmap -Pn -sV --script vuln --script-timeout=120s --max-retries=5 ${target} -oX ${xmlFilePath}`;
    console.log(`Executing vulnerability scan command: ${nmapCommand}`);
    
    // Execute nmap with timeout
    const childProcess = exec(nmapCommand, { 
      timeout: SCAN_TIMEOUT,
      maxBuffer: 1024 * 1024 * 10 // 10MB buffer
    }, async (error, stdout, stderr) => {
      console.log('Nmap execution completed');
      console.log('STDOUT:', stdout);
      console.log('STDERR:', stderr);
      
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
        // Check if XML file was created
        if (!fs.existsSync(xmlFilePath)) {
          throw new Error('XML output file was not created');
        }
        
        // Process XML output
        const scanResult = await processXMLOutput(xmlFilePath, target);
        
        // Cleanup temporary file
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
    
    // Handle process events
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

/**
 * Test function to verify nmap installation
 * @returns {Promise<Object>} - Nmap version information
 */
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

/**
 * Get available nmap scripts
 * @returns {Promise<Object>} - List of available scripts
 */
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
