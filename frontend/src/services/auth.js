import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Storage keys
const TOKEN_KEY = 'qrms_access_token';
const USER_KEY = 'qrms_user';

/**
 * Get stored token
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Get stored user
 */
export const getUser = () => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  const token = getToken();
  return !!token;
};

/**
 * Login with username and password
 */
export const login = async (username, password) => {
  try {
    const response = await axios.post(`${API_BASE}/api/v1/auth/login`, {
      username,
      password
    });
    
    const { access_token, username: user, expires_in } = response.data;
    
    // Store token and user
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify({
      username: user,
      expires_in,
      loginTime: Date.now()
    }));
    
    return { success: true, user };
  } catch (error) {
    console.error('Login error:', error);
    const message = error.response?.data?.detail || 'Error de autenticación';
    return { success: false, error: message };
  }
};

/**
 * Logout - clear stored data
 */
export const logout = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

/**
 * Verify current token
 */
export const verifyToken = async () => {
  const token = getToken();
  if (!token) return false;
  
  try {
    const response = await axios.post(`${API_BASE}/api/v1/auth/verify`, {}, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.status === 200;
  } catch (error) {
    console.error('Token verification failed:', error);
    logout(); // Clear invalid token
    return false;
  }
};

/**
 * Get authenticated axios instance
 */
export const getAuthenticatedApi = () => {
  const token = getToken();
  
  const instance = axios.create({
    baseURL: API_BASE,
    headers: {
      Authorization: token ? `Bearer ${token}` : ''
    }
  });
  
  // Add response interceptor for 401 errors
  instance.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        logout();
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
  
  return instance;
};

export default {
  login,
  logout,
  getToken,
  getUser,
  isAuthenticated,
  verifyToken,
  getAuthenticatedApi
};
