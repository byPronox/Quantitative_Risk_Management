const axios = require('axios');
const nodemailer = require('nodemailer');

// ============================================
// CONFIGURACIÓN
// ============================================

const CONFIG = {
  // Servicio a monitorear
  SERVICE_NAME: 'nmap-scanner-service',
  SERVICE_URL: process.env.NMAP_SERVICE_URL || 'http://nmap-scanner-service:8004',
  HEALTH_ENDPOINT: '/api/v1/health',

  // Intervalo de chequeo
  // MODO SIMULACIÓN: 30 segundos (para pruebas rápidas)
  // MODO PRODUCCIÓN: 30 minutos (1800000 ms)
  CHECK_INTERVAL_MS: process.env.HEALTH_CHECK_INTERVAL_MS || 30000, // 30 segundos por defecto para simulación

  // Configuración de email
  EMAIL_TO: process.env.ALERT_EMAIL || 'fabrikfaf@gmail.com',
  EMAIL_FROM: process.env.EMAIL_FROM || 'qrm.monitor@gmail.com',

  // SMTP Configuration (Gmail)
  SMTP_HOST: process.env.SMTP_HOST || 'smtp.gmail.com',
  SMTP_PORT: process.env.SMTP_PORT || 587,
  SMTP_USER: process.env.SMTP_USER,
  SMTP_PASS: process.env.SMTP_PASS, // App Password de Gmail

  // Reintentos antes de notificar
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 5000, // 5 segundos entre reintentos
};

// ============================================
// ESTADO DEL MONITOR
// ============================================

let serviceState = {
  isHealthy: true,
  consecutiveFailures: 0,
  lastCheckTime: null,
  lastNotificationTime: null,
  totalChecks: 0,
  totalFailures: 0,
};

// ============================================
// CONFIGURACIÓN DE EMAIL
// ============================================

const transporter = nodemailer.createTransport({
  host: CONFIG.SMTP_HOST,
  port: CONFIG.SMTP_PORT,
  secure: false, // true for 465, false for other ports
  auth: {
    user: CONFIG.SMTP_USER,
    pass: CONFIG.SMTP_PASS,
  },
});

// ============================================
// FUNCIONES DE MONITOREO
// ============================================

/**
 * Verifica la salud del servicio
 */
async function checkServiceHealth() {
  try {
    const response = await axios.get(
      `${CONFIG.SERVICE_URL}${CONFIG.HEALTH_ENDPOINT}`,
      { timeout: 5000 }
    );

    return {
      isHealthy: response.status === 200,
      statusCode: response.status,
      data: response.data,
    };
  } catch (error) {
    return {
      isHealthy: false,
      error: error.message,
      code: error.code,
    };
  }
}

/**
 * Envía notificación por email
 */
async function sendEmailNotification(subject, htmlContent) {
  try {
    const info = await transporter.sendMail({
      from: `"QRM Health Monitor" <${CONFIG.EMAIL_FROM}>`,
      to: CONFIG.EMAIL_TO,
      subject: subject,
      html: htmlContent,
    });

    console.log('✅ Email enviado:', info.messageId);
    return true;
  } catch (error) {
    console.error('❌ Error enviando email:', error.message);
    return false;
  }
}

/**
 * Genera HTML para email de alerta
 */
function generateAlertEmail(failureDetails) {
  const timestamp = new Date().toISOString();

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc3545; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
        .content { background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }
        .footer { background: #e9ecef; padding: 15px; border-radius: 0 0 5px 5px; font-size: 12px; }
        .alert-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }
        .stats { background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .stat-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .stat-label { font-weight: bold; }
        .error-details { background: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 3px; margin: 10px 0; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🚨 ALERTA: Servicio Caído</h1>
        </div>
        
        <div class="content">
          <div class="alert-box">
            <h2>⚠️ ${CONFIG.SERVICE_NAME} NO RESPONDE</h2>
            <p>El servicio de escaneo Nmap ha dejado de responder y requiere atención inmediata.</p>
          </div>
          
          <div class="stats">
            <h3>📊 Detalles del Incidente</h3>
            <div class="stat-item">
              <span class="stat-label">Servicio:</span>
              <span>${CONFIG.SERVICE_NAME}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">URL:</span>
              <span>${CONFIG.SERVICE_URL}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Timestamp:</span>
              <span>${timestamp}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Fallos Consecutivos:</span>
              <span>${serviceState.consecutiveFailures}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Total de Chequeos:</span>
              <span>${serviceState.totalChecks}</span>
            </div>
          </div>
          
          <div class="error-details">
            <h3>🔍 Detalles del Error</h3>
            <pre>${JSON.stringify(failureDetails, null, 2)}</pre>
          </div>
          
          <div class="alert-box">
            <h3>🔧 Acciones Recomendadas</h3>
            <ol>
              <li>Verificar logs del contenedor: <code>docker logs nmap-scanner-service</code></li>
              <li>Revisar estado del contenedor: <code>docker ps -a | grep nmap-scanner</code></li>
              <li>Intentar reiniciar: <code>docker-compose restart nmap-scanner-service</code></li>
              <li>Si persiste, revisar configuración y recursos del sistema</li>
            </ol>
          </div>
        </div>
        
        <div class="footer">
          <p>Este es un mensaje automático del sistema de monitoreo QRM.</p>
          <p>Intervalo de chequeo: ${CONFIG.CHECK_INTERVAL_MS / 1000} segundos</p>
        </div>
      </div>
    </body>
    </html>
  `;
}

/**
 * Genera HTML para email de recuperación
 */
function generateRecoveryEmail() {
  const timestamp = new Date().toISOString();

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
        .content { background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }
        .footer { background: #e9ecef; padding: 15px; border-radius: 0 0 5px 5px; font-size: 12px; }
        .success-box { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>✅ RECUPERACIÓN: Servicio Restaurado</h1>
        </div>
        
        <div class="content">
          <div class="success-box">
            <h2>🎉 ${CONFIG.SERVICE_NAME} OPERATIVO</h2>
            <p>El servicio ha sido restaurado y está respondiendo correctamente.</p>
          </div>
          
          <p><strong>Timestamp de recuperación:</strong> ${timestamp}</p>
          <p><strong>Duración del incidente:</strong> Desde ${serviceState.lastNotificationTime || 'N/A'}</p>
        </div>
        
        <div class="footer">
          <p>Sistema de monitoreo QRM - Servicio restaurado exitosamente</p>
        </div>
      </div>
    </body>
    </html>
  `;
}

/**
 * Maneja el resultado del chequeo de salud
 */
async function handleHealthCheckResult(healthResult) {
  serviceState.totalChecks++;
  serviceState.lastCheckTime = new Date().toISOString();

  if (healthResult.isHealthy) {
    // Servicio está saludable
    if (!serviceState.isHealthy) {
      // Recuperación detectada
      console.log('✅ RECUPERACIÓN: Servicio restaurado');
      await sendEmailNotification(
        `✅ RECUPERADO: ${CONFIG.SERVICE_NAME}`,
        generateRecoveryEmail()
      );
    }

    serviceState.isHealthy = true;
    serviceState.consecutiveFailures = 0;
    console.log(`✅ [${serviceState.lastCheckTime}] ${CONFIG.SERVICE_NAME} - Saludable (${serviceState.totalChecks} chequeos)`);

  } else {
    // Servicio tiene problemas
    serviceState.consecutiveFailures++;
    serviceState.totalFailures++;

    console.log(`❌ [${serviceState.lastCheckTime}] ${CONFIG.SERVICE_NAME} - Fallo ${serviceState.consecutiveFailures}/${CONFIG.MAX_RETRIES}`);
    console.log(`   Error: ${healthResult.error || healthResult.code || 'Unknown'}`);

    // Si alcanzamos el máximo de reintentos, notificar
    if (serviceState.consecutiveFailures >= CONFIG.MAX_RETRIES && serviceState.isHealthy) {
      console.log('🚨 ALERTA: Enviando notificación de fallo...');

      const emailSent = await sendEmailNotification(
        `🚨 ALERTA: ${CONFIG.SERVICE_NAME} CAÍDO`,
        generateAlertEmail(healthResult)
      );

      if (emailSent) {
        serviceState.isHealthy = false;
        serviceState.lastNotificationTime = new Date().toISOString();
      }
    }
  }
}

/**
 * Ejecuta el ciclo de monitoreo
 */
async function monitoringLoop() {
  console.log(`\n🔍 Ejecutando chequeo de salud...`);

  const healthResult = await checkServiceHealth();
  await handleHealthCheckResult(healthResult);
}

// ============================================
// INICIALIZACIÓN
// ============================================

async function startMonitoring() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║     🏥 HEALTH MONITOR SERVICE - QRM                        ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('📋 Configuración:');
  console.log(`   • Servicio monitoreado: ${CONFIG.SERVICE_NAME}`);
  console.log(`   • URL: ${CONFIG.SERVICE_URL}${CONFIG.HEALTH_ENDPOINT}`);
  console.log(`   • Intervalo: ${CONFIG.CHECK_INTERVAL_MS / 1000} segundos`);
  console.log(`   • Email destino: ${CONFIG.EMAIL_TO}`);
  console.log(`   • Reintentos antes de alerta: ${CONFIG.MAX_RETRIES}`);
  console.log('');

  // Verificar configuración de email
  if (!CONFIG.SMTP_USER || !CONFIG.SMTP_PASS) {
    console.error('⚠️  ADVERTENCIA: Credenciales SMTP no configuradas');
    console.error('   Configure SMTP_USER y SMTP_PASS en el archivo .env');
    console.error('   Las notificaciones por email NO funcionarán hasta que se configuren');
    console.log('');
  } else {
    console.log('✅ Configuración de email verificada');
    console.log('');
  }

  // Primer chequeo inmediato
  await monitoringLoop();

  // Programar chequeos periódicos
  setInterval(monitoringLoop, CONFIG.CHECK_INTERVAL_MS);

  console.log(`\n✅ Monitor iniciado. Próximo chequeo en ${CONFIG.CHECK_INTERVAL_MS / 1000} segundos...\n`);
}

// Manejo de errores no capturados
process.on('unhandledRejection', (error) => {
  console.error('❌ Error no manejado:', error);
});

process.on('SIGTERM', () => {
  console.log('\n👋 Deteniendo monitor...');
  process.exit(0);
});

// Iniciar el servicio
startMonitoring();
