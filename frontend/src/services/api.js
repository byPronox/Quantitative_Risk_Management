import axios from 'axios';

// Get the Kong Gateway URL from environment variables
const KONG_URL = import.meta.env.VITE_API_URL || 'https://kong-6abab64110usqnlwd.kongcloud.dev';
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Detect if we're in development (localhost)
const isDevelopment = window.location.hostname === 'localhost' || 
                      window.location.hostname === '127.0.0.1' || 
                      window.location.hostname === '';

// In development, use direct backend to avoid ngrok/CORS issues
// In production, use Kong Gateway
const API_BASE_URL = isDevelopment ? BACKEND_URL : KONG_URL;

// Main API instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

// Backend API instance
export const backendApi = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add auth token if available
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Apply same interceptors to backendApi
backendApi.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

backendApi.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
