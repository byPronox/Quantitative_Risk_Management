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

// Funciones para AsyncSoftwareAnalysis
export async function analyzeSoftwareAsync(softwareList, params = {}) {
  try {
    const jobs = [];
    
    // Crear jobs para cada software
    for (const software of softwareList) {
      const job = await addKeywordToQueue(software);
      jobs.push({
        software: software,
        jobId: job.job_id,
        keyword: software
      });
    }
    
    return {
      message: `${jobs.length} análisis en cola`,
      job_ids: jobs.map(j => j.jobId),
      estimated_time: jobs.length * 5, // 5 segundos por job estimado
      jobs: jobs
    };
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
  const pollInterval = 3000; // Poll cada 3 segundos
  let attemptCount = 0;
  const maxAttempts = 20; // Máximo 1 minuto de polling
  
  const poll = async () => {
    attemptCount++;
    progress = Math.min((attemptCount / maxAttempts) * 100, 95);
    
    try {
      // Simular progreso y obtener resultados reales
      const completed = [];
      
      // Por cada job ID, intentar obtener vulnerabilidades
      for (const jobId of jobIds) {
        try {
          // Extraer keyword del jobId o usar un identificador
          const keyword = jobId.split('-')[0] || 'apache'; // Fallback
          const vulnData = await fetchNvdVulnerabilities(keyword);
          
          completed.push({
            jobId: jobId,
            status: 'completed',
            software: keyword,
            vulnerabilities: vulnData.vulnerabilities?.slice(0, 10).map(vuln => ({
              id: vuln.cve.id,
              description: vuln.cve.descriptions?.[0]?.value || 'No description',
              severity: vuln.cve.metrics?.cvssMetricV31?.[0]?.cvssData?.baseSeverity || 'UNKNOWN',
              score: vuln.cve.metrics?.cvssMetricV31?.[0]?.cvssData?.baseScore || 0,
              published: vuln.cve.published
            })) || []
          });
        } catch (error) {
          completed.push({
            jobId: jobId,
            status: 'failed',
            error: error.message
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
      
      // Continuar polling
      setTimeout(poll, pollInterval);
      
    } catch (error) {
      callback({
        error: error.message,
        progress: progress
      });
    }
  };
  
  // Iniciar polling
  setTimeout(poll, 1000); // Esperar 1 segundo antes del primer poll
}
