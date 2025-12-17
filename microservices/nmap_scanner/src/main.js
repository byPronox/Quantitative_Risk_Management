import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import routes from './routes.js';
import { startConsumer } from './consumer.js';

// Start RabbitMQ Consumer - DISABLED: Consumer now starts manually via API endpoint
// startConsumer();

// Create Express app
const app = express();

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(',') : '*',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging middleware
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path} - IP: ${req.ip}`);
  next();
});

// API routes
app.use('/api/v1', routes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Nmap Scanner Service',
    version: '1.0.0',
    description: 'Microservice for vulnerability scanning using nmap',
    status: 'running',
    endpoints: {
      scan: 'POST /api/v1/scan',
      test: 'GET /api/v1/test',
      scripts: 'GET /api/v1/scripts',
      validate: 'GET /api/v1/validate/:target',
      status: 'GET /api/v1/status',
      health: 'GET /api/v1/health'
    },
    documentation: '/api/v1/docs',
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    path: req.originalUrl,
    method: req.method,
    timestamp: new Date().toISOString()
  });
});

// Global error handler
app.use((error, req, res, next) => {
  console.error('Global error handler:', error);

  res.status(500).json({
    error: 'Internal server error',
    details: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
    timestamp: new Date().toISOString()
  });
});

// Server configuration
const PORT = process.env.PORT || 8004;
const HOST = process.env.HOST || '0.0.0.0';

// Start server
const server = app.listen(PORT, HOST, () => {
  console.log(`🚀 Nmap Scanner Service started`);
  console.log(`📡 Server running on http://${HOST}:${PORT}`);
  console.log(`🔍 Nmap command: nmap -sV --script vuln [TARGET] -oX scan_result.xml`);
  console.log(`⏰ Scan timeout: 5 minutes`);
  console.log(`🚦 Rate limit: 10 requests per 15 minutes`);
  console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🕐 Started at: ${new Date().toISOString()}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

export default app;
