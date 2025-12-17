import { backendApi } from './api';

/**
 * Nmap Scanner Service
 * Handles async queue operations for Nmap scans
 */

// Add IP to scan queue
export const addIpToQueue = async (targetIp) => {
    const response = await backendApi.post('/api/v1/nmap/queue/job', null, {
        params: { target_ip: targetIp }
    });
    return response.data;
};

// Get all queue results
export const getAllQueueResults = async () => {
    const response = await backendApi.get('/api/v1/nmap/queue/results/all');
    return response.data;
};

// Get queue status
export const getQueueStatus = async () => {
    const response = await backendApi.get('/api/v1/nmap/queue/status');
    return response.data;
};

// Get specific job result
export const getJobResult = async (jobId) => {
    const response = await backendApi.get(`/api/v1/nmap/queue/results/${jobId}`);
    return response.data;
};

// Get all jobs from database
export const getDatabaseJobs = async () => {
    const response = await backendApi.get('/api/v1/nmap/database/jobs');
    return response.data;
};

// Get scan results for a job
export const getScanResults = async (jobId) => {
    const response = await backendApi.get(`/api/v1/nmap/database/results/${jobId}`);
    return response.data;
};

// Health check
export const checkHealth = async () => {
    const response = await backendApi.get('/api/v1/nmap/health');
    return response.data;
};

// Consumer control functions
export const startConsumer = async () => {
    const response = await backendApi.post('/api/v1/nmap/queue/consumer/start');
    return response.data;
};

export const stopConsumer = async () => {
    const response = await backendApi.post('/api/v1/nmap/queue/consumer/stop');
    return response.data;
};

export const getConsumerStatus = async () => {
    const response = await backendApi.get('/api/v1/nmap/queue/consumer/status');
    return response.data;
};
