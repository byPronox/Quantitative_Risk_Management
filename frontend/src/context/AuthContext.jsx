import { createContext, useContext, useState, useEffect } from 'react';
import { login as authLogin, logout as authLogout, getUser, isAuthenticated, verifyToken } from '../services/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Check auth status on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (isAuthenticated()) {
        const isValid = await verifyToken();
        if (isValid) {
          const userData = getUser();
          setUser(userData);
          setIsLoggedIn(true);
        } else {
          setUser(null);
          setIsLoggedIn(false);
        }
      }
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = async (username, password) => {
    const result = await authLogin(username, password);
    if (result.success) {
      const userData = getUser();
      setUser(userData);
      setIsLoggedIn(true);
    }
    return result;
  };

  const logout = () => {
    authLogout();
    setUser(null);
    setIsLoggedIn(false);
  };

  const value = {
    user,
    isLoggedIn,
    loading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
