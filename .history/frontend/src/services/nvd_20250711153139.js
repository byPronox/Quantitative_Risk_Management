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
  let progress = 0;
  const pollInterval = 2000; // Poll cada 2 segundos
  let attemptCount = 0;
  const maxAttempts = 15; // Máximo 30 segundos de polling
  
  const poll = async () => {
    attemptCount++;
    progress = Math.min((attemptCount / maxAttempts) * 100, 95);
    
    try {
      const completed = [];
      
      // Procesar cada job usando Kong API directamente
      for (const jobId of jobIds) {
        try {
          // Extraer keyword del jobId
          const keyword = jobId.split('-')[0] || 'apache';
          
          // Usar Kong para obtener vulnerabilidades
          const vulnData = await fetchNvdVulnerabilities(keyword);
          
          completed.push({
            jobId: jobId,
            status: 'completed',
            software: keyword,
            vulnerabilities: vulnData.vulnerabilities?.slice(0, 8).map(vuln => ({
              id: vuln.cve.id,
              description: vuln.cve.descriptions?.[0]?.value?.substring(0, 150) + '...' || 'No description',
              severity: vuln.cve.metrics?.cvssMetricV31?.[0]?.cvssData?.baseSeverity || 
                       vuln.cve.metrics?.cvssMetricV30?.[0]?.cvssData?.baseSeverity || 'UNKNOWN',
              score: vuln.cve.metrics?.cvssMetricV31?.[0]?.cvssData?.baseScore || 
                     vuln.cve.metrics?.cvssMetricV30?.[0]?.cvssData?.baseScore || 0,
              published: vuln.cve.published
            })) || [],
            totalFound: vulnData.totalResults || 0
          });
        } catch (error) {
          console.warn(`Failed to get results for ${jobId}:`, error);
          completed.push({
            jobId: jobId,
            status: 'failed',
            software: jobId.split('-')[0],
            error: `Failed to fetch vulnerabilities: ${error.message}`
          });
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
  setTimeout(poll, 500);
}
