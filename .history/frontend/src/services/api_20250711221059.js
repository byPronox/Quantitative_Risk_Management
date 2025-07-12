import axios from "axios";

// Backend URL Configuration
const getBaseURL = (useBackend = false) => {
  // For queue consumer endpoints, use local backend
  if (useBackend) {
    const backendURL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
    console.log(`Using backend URL: ${backendURL}`);
    return backendURL;
  }
  
  // For NVD API calls, use Kong Gateway
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

// Separate API instance for backend endpoints (queue management)
const backendApi = axios.create({
  baseURL: getBaseURL(true), // Use backend URL
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

// Request interceptor for backend API
backendApi.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} backend request to:`, config.baseURL + config.url);
    return config;
  },
  (error) => {
    console.error('Backend request error:', error);
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

// Response interceptor for backend API
backendApi.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Backend API Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    return Promise.reject(error);
  }
);

export default api;
export { backendApi };