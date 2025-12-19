import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { scanIP, validateIP, validateHostname, testNmapInstallation, getAvailableScripts } from './scanner.js';
import queueService from './queue_service.js';
import databaseService from './database_service.js';
import { startConsumer, stopConsumer, isConsumerRunning } from './consumer.js';

const router = express.Router();

// Consumer state tracking
// Consumer state tracking handled in consumer.js

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
      ...scanResult,
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

// ============================================
// QUEUE ENDPOINTS (Async Processing)
// ============================================

/**
 * POST /queue/job - Add scan job to queue
 * Query: ?target_ip=192.168.1.1
 * Returns: Job ID and status
 */
router.post('/queue/job', async (req, res) => {
  try {
    const targetIp = req.query.target_ip || req.body.target_ip;

    if (!targetIp) {
      return res.status(400).json({
        success: false,
        error: 'Missing target_ip parameter',
        details: 'target_ip is required in query params or body'
      });
    }

    if (!validateIP(targetIp) && !validateHostname(targetIp)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid target format',
        details: 'Target must be a valid IP address or hostname'
      });
    }

    const result = await queueService.addJob(targetIp, req.body.options || {});
    res.status(201).json(result);

  } catch (error) {
    console.error('[Queue] Error adding job:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to add job to queue',
      details: error.message
    });
  }
});

/**
 * GET /queue/status - Get queue status
 * Returns: Queue statistics
 */
router.get('/queue/status', async (req, res) => {
  try {
    const status = await queueService.getQueueStatus();
    res.json(status);
  } catch (error) {
    console.error('[Queue] Error getting status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get queue status',
      details: error.message
    });
  }
});

/**
 * GET /queue/results/all - Get all job results
 * Returns: All jobs from database
 */
router.get('/queue/results/all', async (req, res) => {
  try {
    const results = await queueService.getAllJobResults();
    res.json(results);
  } catch (error) {
    console.error('[Queue] Error getting all results:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get job results',
      details: error.message
    });
  }
});

/**
 * GET /queue/results/:jobId - Get specific job result
 * Returns: Job details with port results
 */
router.get('/queue/results/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;
    const result = await queueService.getJobResult(jobId);

    if (!result.success) {
      return res.status(404).json(result);
    }

    res.json(result);
  } catch (error) {
    console.error('[Queue] Error getting job result:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get job result',
      details: error.message
    });
  }
});

/**
 * GET /database/jobs - Get all jobs from database
 * Returns: All jobs
 */
router.get('/database/jobs', async (req, res) => {
  try {
    const jobs = await databaseService.getAllJobs();
    res.json({
      success: true,
      total: jobs.length,
      jobs: jobs
    });
  } catch (error) {
    console.error('[Database] Error getting jobs:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get jobs from database',
      details: error.message
    });
  }
});

/**
 * GET /database/results/:jobId - Get scan results for a job
 * Returns: Port results
 */
router.get('/database/results/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;
    const results = await databaseService.getScanResults(jobId);
    res.json({
      success: true,
      job_id: jobId,
      total: results.length,
      results: results
    });
  } catch (error) {
    console.error('[Database] Error getting scan results:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get scan results',
      details: error.message
    });
  }
});

// ============================================
// CONSUMER CONTROL ENDPOINTS
// ============================================

/**
 * POST /queue/consumer/start - Start the RabbitMQ consumer
 * Returns: Success status
 */
router.post('/queue/consumer/start', async (req, res) => {
  try {
    if (isConsumerRunning()) {
      return res.json({
        success: true,
        message: 'Consumer is already running',
        status: 'running'
      });
    }

    // Start consumer (don't await - let it run in background)
    startConsumer().catch(err => {
      console.error('[Consumer] Error in background consumer:', err);
    });

    // Give it a moment to connect
    await new Promise(resolve => setTimeout(resolve, 2000));

    res.json({
      success: true,
      message: 'Consumer started successfully',
      status: 'running'
    });
  } catch (error) {
    console.error('[Consumer] Error starting consumer:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to start consumer',
      details: error.message
    });
  }
});

/**
 * POST /queue/consumer/stop - Stop the RabbitMQ consumer
 * Returns: Success status
 */
router.post('/queue/consumer/stop', async (req, res) => {
  try {
    await stopConsumer();
    res.json({
      success: true,
      message: 'Consumer stopped successfully',
      status: 'stopped'
    });
  } catch (error) {
    console.error('[Consumer] Error stopping consumer:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to stop consumer',
      details: error.message
    });
  }
});

/**
 * GET /queue/consumer/status - Get consumer status
 * Returns: Consumer running status
 */
router.get('/queue/consumer/status', async (req, res) => {
  try {
    const running = isConsumerRunning();
    res.json({
      success: true,
      running: running,
      status: running ? 'running' : 'stopped',
      description: running
        ? 'Consumer is actively processing jobs from the queue'
        : 'Consumer is stopped. Start it to process queued jobs'
    });
  } catch (error) {
    console.error('[Consumer] Error getting consumer status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get consumer status',
      details: error.message
    });
  }
});

// ============================================
// EXISTING ENDPOINTS
// ============================================

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
      queueJob: 'POST /queue/job',
      queueStatus: 'GET /queue/status',
      queueResults: 'GET /queue/results/all',
      test: 'GET /test',
      scripts: 'GET /scripts',
      validate: 'GET /validate/:target',
      status: 'GET /status',
      health: 'GET /health'
    },
    configuration: {
      scanTimeout: '20 minutes',
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

    // Test database connection
    await databaseService.connect();

    // Test queue connection
    const queueStatus = await queueService.getQueueStatus();

    res.json({
      status: 'healthy',
      service: 'Nmap Scanner Service',
      version: '1.0.0',
      nmap: {
        installed: nmapTest.installed,
        version: nmapTest.version
      },
      database: {
        connected: databaseService.isConnected,
        status: 'healthy'
      },
      queue: {
        connected: queueStatus.success,
        status: queueStatus.status
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      service: 'Nmap Scanner Service',
      error: 'Service components not available',
      details: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

export default router;

