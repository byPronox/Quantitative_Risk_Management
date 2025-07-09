import axios from "axios";

// Backend URL Configuration
const getBaseURL = () => {
  // Check environment variable first
  const envURL = import.meta.env.VITE_API_URL;
  
  if (envURL) {
    console.log(`Using configured API URL: ${envURL}`);
    return envURL;
  }
  
  // Default to local backend for development
  console.log('Using default backend URL: http://localhost:8000');
  return "http://localhost:8000";
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'X-Client': 'quantitative-risk-frontend'
  }
});

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to:`, config.baseURL + config.url);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    return Promise.reject(error);
  }
);

export default api;