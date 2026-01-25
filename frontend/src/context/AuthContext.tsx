/**
 * Authentication Context - Manages global authentication state
 */

import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { login as loginAPI, logout as logoutAPI, getSession } from '@/services/authService';
import type { User } from '@/types/models';
import type { SessionInfoWithoutToken } from '@/types/models';
import { isAPIError } from '@/types/api';

/**
 * Authentication state shape
 */
export interface AuthState {
  /** Currently authenticated user (null if not authenticated) */
  user: User | null;
  /** Current session information (null if not authenticated) */
  session: SessionInfoWithoutToken | null;
  /** Whether auth state is being initialized */
  isLoading: boolean;
  /** Whether a login/logout operation is in progress */
  isAuthenticating: boolean;
}

/**
 * Authentication context value
 */
export interface AuthContextValue extends AuthState {
  /** Login with username and password */
  login: (username: string, password: string) => Promise<void>;
  /** Logout and clear session */
  logout: () => Promise<void>;
  /** Refresh session data */
  refreshSession: () => Promise<void>;
}

/**
 * Default context value (throws error if used outside provider)
 */
const defaultContextValue: AuthContextValue = {
  user: null,
  session: null,
  isLoading: true,
  isAuthenticating: false,
  login: async () => {
    throw new Error('AuthContext not initialized');
  },
  logout: async () => {
    throw new Error('AuthContext not initialized');
  },
  refreshSession: async () => {
    throw new Error('AuthContext not initialized');
  },
};

/**
 * Authentication context
 */
// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue>(defaultContextValue);

/**
 * Props for AuthProvider
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 *
 * Manages authentication state and provides auth methods to child components.
 * Automatically checks for existing session on mount.
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    session: null,
    isLoading: true,
    isAuthenticating: false,
  });

  /**
   * Refresh session data from server
   */
  const refreshSession = useCallback(async () => {
    try {
      const sessionData = await getSession();
      setAuthState({
        user: sessionData.user,
        session: sessionData.session,
        isLoading: false,
        isAuthenticating: false,
      });
    } catch (error) {
      // Session invalid or expired
      setAuthState({
        user: null,
        session: null,
        isLoading: false,
        isAuthenticating: false,
      });
    }
  }, []);

  /**
   * Initialize auth state on mount
   */
  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  /**
   * Login with credentials
   */
  const login = useCallback(async (username: string, password: string) => {
    setAuthState(prev => ({ ...prev, isAuthenticating: true }));

    try {
      const response = await loginAPI(username, password);

      setAuthState({
        user: response.user,
        session: {
          expires_at: response.session.expires_at,
        },
        isLoading: false,
        isAuthenticating: false,
      });
    } catch (error) {
      setAuthState(prev => ({ ...prev, isAuthenticating: false }));

      // Re-throw error so component can display it
      if (isAPIError(error)) {
        throw new Error(error.detail);
      }
      throw new Error('Login failed. Please try again.');
    }
  }, []);

  /**
   * Logout and clear session
   */
  const logout = useCallback(async () => {
    setAuthState(prev => ({ ...prev, isAuthenticating: true }));

    try {
      await logoutAPI();
    } catch (error) {
      // Even if logout API fails, clear local state
      console.error('Logout error:', error);
    } finally {
      setAuthState({
        user: null,
        session: null,
        isLoading: false,
        isAuthenticating: false,
      });
    }
  }, []);

  const contextValue: AuthContextValue = {
    ...authState,
    login,
    logout,
    refreshSession,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
