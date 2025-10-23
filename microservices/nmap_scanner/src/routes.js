import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { scanIP, validateIP, validateHostname, testNmapInstallation, getAvailableScripts } from './scanner.js';

const router = express.Router();

// Rate limiting configuration
const scanLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // Limit each IP to 10 scan requests per windowMs
  message: {
    error: 'Too many scan requests',
    details: 'Maximum 10 scans per 15 minutes allowed'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * POST /scan - Main scanning endpoint
 * Body: { ip: string }
 * Returns: Structured scan result
 */
router.post('/scan', scanLimiter, async (req, res) => {
  const startTime = Date.now();
  console.log(`[${new Date().toISOString()}] Scan request received:`, req.body);
  
  const { ip } = req.body;
  
  // Validate input
  if (!ip) {
    console.log('Error: Missing IP parameter');
    return res.status(400).json({ 
      error: 'Missing IP parameter',
      details: 'IP address or hostname is required in request body'
    });
  }
  
  if (!validateIP(ip) && !validateHostname(ip)) {
    console.log(`Error: Invalid IP format: ${ip}`);
    return res.status(400).json({ 
      error: 'Invalid IP format',
      details: 'Target must be a valid IP address or hostname'
    });
  }
  
  try {
    console.log(`Starting scan for target: ${ip}`);
    const scanResult = await scanIP(ip);
    
    const duration = Date.now() - startTime;
    console.log(`Scan completed for ${ip} in ${duration}ms`);
    
    res.json({
      success: true,
      data: scanResult,
      scanDuration: `${duration}ms`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`Scan failed for ${ip} after ${duration}ms:`, error);
    
    res.status(500).json({
      success: false,
      error: error.error || 'Scan failed',
      details: error.details || error.message,
      target: ip,
      scanDuration: `${duration}ms`,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /test - Test nmap installation
 * Returns: Installation status and version
 */
router.get('/test', async (req, res) => {
  try {
    console.log('Testing nmap installation...');
    const result = await testNmapInstallation();
    
    res.json({
      success: true,
      data: result,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Nmap test failed:', error);
    res.status(500).json({
      success: false,
      error: error.error || 'Nmap test failed',
      details: error.details || error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /scripts - Get available vulnerability scripts
 * Returns: List of available scripts
 */
router.get('/scripts', async (req, res) => {
  try {
    console.log('Getting available nmap scripts...');
    const result = await getAvailableScripts();
    
    res.json({
      success: true,
      data: result,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Failed to get scripts:', error);
    res.status(500).json({
      success: false,
      error: error.error || 'Failed to get scripts',
      details: error.details || error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /validate/:target - Validate IP or hostname format
 * Returns: Validation result
 */
router.get('/validate/:target', (req, res) => {
  const { target } = req.params;
  
  const isValidIP = validateIP(target);
  const isValidHostname = validateHostname(target);
  
  res.json({
    target: target,
    isValidIP: isValidIP,
    isValidHostname: isValidHostname,
    isValid: isValidIP || isValidHostname,
    timestamp: new Date().toISOString()
  });
});

/**
 * GET /status - Service status and configuration
 * Returns: Service information
 */
router.get('/status', (req, res) => {
  res.json({
    service: 'Nmap Scanner Service',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      scan: 'POST /scan',
      test: 'GET /test',
      scripts: 'GET /scripts',
      validate: 'GET /validate/:target',
      status: 'GET /status',
      health: 'GET /health'
    },
    configuration: {
      scanTimeout: '5 minutes',
      rateLimit: '10 requests per 15 minutes',
      supportedTargets: ['IP addresses', 'hostnames'],
      nmapCommand: 'nmap -sV --script vuln [TARGET] -oX scan_result.xml'
    },
    timestamp: new Date().toISOString()
  });
});

/**
 * GET /health - Health check endpoint
 * Returns: Health status
 */
router.get('/health', async (req, res) => {
  try {
    // Test nmap installation
    const nmapTest = await testNmapInstallation();
    
    res.json({
      status: 'healthy',
      service: 'Nmap Scanner Service',
      version: '1.0.0',
      nmap: {
        installed: nmapTest.installed,
        version: nmapTest.version
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      service: 'Nmap Scanner Service',
      error: 'Nmap not available',
      details: error.details || error.message,
      timestamp: new Date().toISOString()
    });
  }
});

export default router;
