/**
 * API Client - Base fetch wrapper with error handling
 */

import { APIError } from '@/types/api';

/**
 * Base API configuration
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * HTTP request options
 */
interface RequestOptions extends RequestInit {
  timeout?: number;
}

/**
 * Fetch wrapper with timeout and error handling
 */
async function fetchWithTimeout(
  url: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { timeout = 120000, ...fetchOptions } = options; // 2 minute default timeout

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      credentials: 'include', // Include cookies for session authentication
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if ((error as Error).name === 'AbortError') {
      throw new APIError(408, 'Request timeout', 'TIMEOUT');
    }

    throw new APIError(0, 'Network error. Please check your connection.', 'NETWORK_ERROR');
  }
}

/**
 * Parse API response
 */
async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');

  // Handle non-JSON responses (like CSV exports)
  if (contentType && !contentType.includes('application/json')) {
    return response as any;
  }

  try {
    const data = await response.json();

    if (!response.ok) {
      // Extract error message from response
      const errorMessage = data.detail || data.message || 'An error occurred';
      const errorCode = data.error_code || undefined;
      throw new APIError(response.status, errorMessage, errorCode);
    }

    return data;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    // JSON parse error
    throw new APIError(
      response.status,
      'Invalid response from server',
      'PARSE_ERROR'
    );
  }
}

/**
 * Generic API request function
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const mergedOptions: RequestOptions = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  const response = await fetchWithTimeout(url, mergedOptions);

  // Just parse the response - let AuthContext/ProtectedRoute handle redirects
  return parseResponse<T>(response);
}

/**
 * API client methods
 */
export const apiClient = {
  /**
   * GET request
   */
  get: <T>(endpoint: string, options?: RequestOptions): Promise<T> => {
    return apiRequest<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  },

  /**
   * POST request
   */
  post: <T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> => {
    return apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  /**
   * PUT request
   */
  put: <T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> => {
    return apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  /**
   * DELETE request
   */
  delete: <T>(endpoint: string, options?: RequestOptions): Promise<T> => {
    return apiRequest<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
  },

  /**
   * Download file (for CSV export)
   */
  download: async (endpoint: string): Promise<Blob> => {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetchWithTimeout(url, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await parseResponse(response);
      throw error;
    }

    return response.blob();
  },
};

export default apiClient;
