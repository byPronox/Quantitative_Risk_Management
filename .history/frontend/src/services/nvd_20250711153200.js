import api from "./api";

export async function fetchNvdVulnerabilities(keyword = "apache") {
  // Use Kong proxy to NVD API directly
  const response = await api.get("/nvd/cves/2.0", {
    params: { keywordSearch: keyword }
  });
  return response.data;
}

export async function analyzeNvdRisk() {
  const response = await api.post("/nvd/analyze_risk");
  return response.data;
}

export async function addKeywordToQueue(keyword) {
  const response = await api.post("/nvd/queue/add", {
    keyword: keyword
  });
  return response.data;
}

// Funciones para AsyncSoftwareAnalysis usando RabbitMQ
export async function analyzeSoftwareAsync(softwareList, params = {}) {
  try {
    // Usar el endpoint del backend que maneja RabbitMQ
    const response = await api.post("/nvd/analyze_software_async", {
      software_list: softwareList,
      metadata: params
    });
    
    return response.data;
  } catch (error) {
    console.error('Error starting async analysis:', error);
    throw error;
  }
}

export async function getQueueStatus() {
  try {
    const response = await api.get("/nvd/queue/status");
    return {
      pending_jobs: response.data.queue_size || 0,
      processing_jobs: 0, // Kong no proporciona esto directamente
      completed_jobs: response.data.total_vulnerabilities || 0,
      queue_health: response.data.connected ? 'healthy' : 'unhealthy',
      keywords: response.data.keywords || [],
      ...response.data
    };
  } catch (error) {
    console.error('Error fetching queue status:', error);
    return {
      pending_jobs: 0,
      processing_jobs: 0,
      completed_jobs: 0,
      queue_health: 'unhealthy',
      keywords: []
    };
  }
}

export function pollAnalysisResults(jobIds, callback) {
  const pollInterval = 3000; // Poll cada 3 segundos
  let attemptCount = 0;
  const maxAttempts = 20; // Máximo 60 segundos de polling
  
  const poll = async () => {
    attemptCount++;
    const progress = Math.min((attemptCount / maxAttempts) * 100, 95);
    
    try {
      const completed = [];
      
      // Usar el endpoint del backend para obtener resultados de cada job
      for (const jobId of jobIds) {
        try {
          const response = await api.get(`/nvd/results/${jobId}`);
          const result = response.data;
          
          if (result.status === 'completed' || result.status === 'failed') {
            completed.push({
              jobId: jobId,
              status: result.status,
              software: result.software || jobId.split('-')[0],
              vulnerabilities: result.vulnerabilities || [],
              totalFound: result.total_found || 0,
              error: result.error
            });
          }
        } catch (error) {
          // Si el job no está listo, continuar esperando
          if (error.response?.status === 404) {
            console.log(`Job ${jobId} still processing...`);
          } else {
            console.warn(`Error fetching results for ${jobId}:`, error);
            completed.push({
              jobId: jobId,
              status: 'failed',
              software: jobId.split('-')[0],
              error: `Failed to fetch results: ${error.message}`
            });
          }
        }
      }
      
      // Llamar callback con resultados
      callback({
        progress: progress,
        completed: completed
      });
      
      // Si completamos todos los jobs o llegamos al máximo de intentos
      if (completed.length === jobIds.length || attemptCount >= maxAttempts) {
        callback({
          progress: 100,
          completed: completed
        });
        return;
      }
      
      // Continuar polling si no hemos terminado
      setTimeout(poll, pollInterval);
      
    } catch (error) {
      callback({
        error: error.message,
        progress: progress
      });
    }
  };
  
  // Iniciar polling después de un breve delay
  setTimeout(poll, 1000);
}
