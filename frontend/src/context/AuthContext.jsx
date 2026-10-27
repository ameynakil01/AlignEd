import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  getAuthToken,
  setAuthToken,
  loginUser,
  registerUser,
  getDashboardState
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(getAuthToken());
  const [dashboardState, setDashboardState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshDashboardState = useCallback(async () => {
    try {
      const state = await getDashboardState();
      if (state) {
        setUser(state.user);
        setDashboardState(state);
      } else {
        setUser(null);
        setDashboardState(null);
      }
    } catch (err) {
      console.warn('Failed to refresh dashboard state:', err);
    }
  }, []);

  useEffect(() => {
    async function initAuth() {
      const existingToken = getAuthToken();
      if (existingToken) {
        try {
          const state = await getDashboardState();
          if (state) {
            setUser(state.user);
            setDashboardState(state);
          } else {
            setAuthToken(null);
            setToken(null);
          }
        } catch (err) {
          console.warn('Auto-login session expired:', err);
          setAuthToken(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    }
    initAuth();
  }, []);

  const login = async (credentials) => {
    const res = await loginUser(credentials);
    setToken(res.access_token);
    setUser(res.user);
    await refreshDashboardState();
    return res;
  };

  const register = async (userData) => {
    const res = await registerUser(userData);
    setToken(res.access_token);
    setUser(res.user);
    await refreshDashboardState();
    return res;
  };

  const logout = () => {
    setAuthToken(null);
    setToken(null);
    setUser(null);
    setDashboardState(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        dashboardState,
        isLoading,
        login,
        register,
        logout,
        refreshDashboardState,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

