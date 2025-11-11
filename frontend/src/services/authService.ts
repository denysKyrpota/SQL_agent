/**
 * Authentication Service - API calls for authentication workflow
 */

import apiClient from './apiClient';
import type {
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  SessionResponse,
} from '@/types/api';

/**
 * Login with username and password
 * POST /auth/login
 */
export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const request: LoginRequest = {
    username,
    password,
  };

  return apiClient.post<LoginResponse>('/auth/login', request);
}

/**
 * Logout and invalidate current session
 * POST /auth/logout
 */
export async function logout(): Promise<LogoutResponse> {
  return apiClient.post<LogoutResponse>('/auth/logout');
}

/**
 * Get current session information
 * GET /auth/session
 */
export async function getSession(): Promise<SessionResponse> {
  return apiClient.get<SessionResponse>('/auth/session');
}

/**
 * Check if user is authenticated by validating session
 */
export async function checkAuth(): Promise<boolean> {
  try {
    await getSession();
    return true;
  } catch (error) {
    return false;
  }
}
