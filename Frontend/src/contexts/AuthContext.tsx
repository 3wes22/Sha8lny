/**
 * Authentication Context
 *
 * Provides authentication state and methods across the application.
 * Handles login, logout, registration, and token management.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  authApi,
  userApi,
  tokenStorage,
  ApiError,
} from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

// ============================================================================
// Types
// ============================================================================

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// ============================================================================
// Context
// ============================================================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ============================================================================
// Provider
// ============================================================================

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });
  const { toast } = useToast();
  const navigate = useNavigate();

  // Check for existing session on mount
  useEffect(() => {
    const initAuth = async () => {
      if (tokenStorage.isAuthenticated()) {
        try {
          const user = await userApi.getProfile();
          setState({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token invalid, clear it
          tokenStorage.clearTokens();
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    initAuth();
  }, []);

  // Login handler
  const login = useCallback(async (data: LoginRequest) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const response = await authApi.login(data);
      // Backend returns { tokens: { access, refresh }, user, message }
      tokenStorage.setTokens(response.tokens.access, response.tokens.refresh);

      setState({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
      });

      toast({
        title: 'Welcome back!',
        description: `Logged in as ${response.user.full_name}`,
      });

      navigate('/dashboard');
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));

      if (error instanceof ApiError) {
        const message = error.status === 401
          ? 'Invalid email or password'
          : 'Login failed. Please try again.';

        toast({
          title: 'Login Failed',
          description: message,
          variant: 'destructive',
        });
      }
      throw error;
    }
  }, [navigate, toast]);

  // Register handler
  const register = useCallback(async (data: RegisterRequest) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const response = await authApi.register(data);
      // Backend returns { tokens: { access, refresh }, user, message }
      tokenStorage.setTokens(response.tokens.access, response.tokens.refresh);

      setState({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
      });

      toast({
        title: 'Account created!',
        description: 'Welcome to Sha8lny. Let\'s get started!',
      });

      navigate('/dashboard');
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));

      if (error instanceof ApiError) {
        let message = 'Registration failed. Please try again.';

        if (error.status === 400 && error.data) {
          // Extract validation errors
          const errors = error.data as Record<string, string[]>;
          const firstError = Object.values(errors)[0];
          if (firstError && firstError[0]) {
            message = firstError[0];
          }
        }

        toast({
          title: 'Registration Failed',
          description: message,
          variant: 'destructive',
        });
      }
      throw error;
    }
  }, [navigate, toast]);

  // Logout handler
  const logout = useCallback(async () => {
    try {
      const refreshToken = tokenStorage.getRefreshToken();
      await authApi.logout(refreshToken || undefined);
    } catch {
      // Ignore logout errors
    } finally {
      tokenStorage.clearTokens();
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });

      toast({
        title: 'Logged out',
        description: 'See you next time!',
      });

      navigate('/login');
    }
  }, [navigate, toast]);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    if (!tokenStorage.isAuthenticated()) return;

    try {
      const user = await userApi.getProfile();
      setState(prev => ({ ...prev, user }));
    } catch {
      // Silently fail
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// ============================================================================
// Protected Route Component
// ============================================================================

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
