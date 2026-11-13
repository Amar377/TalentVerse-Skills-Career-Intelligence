import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { api } from '../services/api';
import { useToast } from './ToastContext';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  loginDemo: () => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('talentverse_token'));
  const [isLoading, setIsLoading] = useState(true);
  const { success, error } = useToast();

  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem('talentverse_token');
      if (storedToken) {
        try {
          const userData = await api.auth.getMe();
          setUser(userData);
        } catch {
          console.warn('Session expired or invalid, clearing token');
          localStorage.removeItem('talentverse_token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    }
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.auth.login({ email, password });
      localStorage.setItem('talentverse_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      success('Welcome back!', `Signed in as ${res.user.full_name || res.user.email}`);
    } catch (err: any) {
      error('Sign in failed', err.message || 'Please check your credentials.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setIsLoading(true);
    try {
      const res = await api.auth.register({ email, password, full_name: fullName });
      localStorage.setItem('talentverse_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      success('Account created!', `Welcome to TalentVerse, ${fullName}!`);
    } catch (err: any) {
      error('Registration failed', err.message || 'Could not complete registration.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const loginDemo = async () => {
    setIsLoading(true);
    try {
      const res = await api.auth.demoLogin();
      localStorage.setItem('talentverse_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      success('Demo Workspace Activated', 'Exploring TalentVerse 2.0 with full interactive capabilities.');
    } catch (err: any) {
      error('Demo login failed', err.message || 'Could not connect to sandbox.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('talentverse_token');
    setToken(null);
    setUser(null);
    success('Signed out', 'You have been safely signed out.');
  };

  const refreshUser = async () => {
    try {
      const userData = await api.auth.getMe();
      setUser(userData);
    } catch (err) {
      console.error('Failed to refresh user', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        loginDemo,
        logout,
        refreshUser,
      }}
    >
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
