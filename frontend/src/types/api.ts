/**
 * API request and response types.
 * These types define the contract between frontend and backend.
 */

import type {
  ISO8601Timestamp,
  PaginationMetadata,
  PaginationParams,
  QueryStatus,
} from "./common";
import type {
  KBReloadStats,
  MetricRow,
  MetricsSummary,
  QueryAttempt,
  QueryAttemptDetail,
  QueryResults,
  SchemaSnapshot,
  ServiceStatus,
  SessionInfo,
  SessionInfoWithoutToken,
  SimplifiedQueryAttempt,
  User,
} from "./models";

// ============================================================================
// Authentication API
// ============================================================================

/**
 * Request body for POST /auth/login
 */
export interface LoginRequest {
  /** Username for authentication */
  username: string;
  /** User password (min 8 characters) */
  password: string;
}

/**
 * Response for POST /auth/login
 */
export interface LoginResponse {
  /** Authenticated user information */
  user: User;
  /** Session details including token */
  session: SessionInfo;
}

/**
 * Response for POST /auth/logout
 */
export interface LogoutResponse {
  /** Success message */
  message: string;
}

/**
 * Response for GET /auth/session
 */
export interface SessionResponse {
  /** Current user information */
  user: User;
  /** Session details (without token) */
  session: SessionInfoWithoutToken;
}

// ============================================================================
// Query Workflow API
// ============================================================================

/**
 * Request body for POST /queries
 */
export interface CreateQueryRequest {
  /** Natural language query to convert to SQL */
  natural_language_query: string;
}

/**
 * Response for POST /queries
 */
export interface QueryAttemptResponse extends QueryAttempt {}

/**
 * Response for GET /queries/{id}
 */
export interface QueryAttemptDetailResponse extends QueryAttemptDetail {}

/**
 * Query parameters for GET /queries
 */
export interface QueryListParams extends PaginationParams {
  /** Optional status filter */
  status?: QueryStatus;
}

/**
 * Response for GET /queries
 */
export interface QueryListResponse {
  /** List of query attempts */
  queries: SimplifiedQueryAttempt[];
  /** Pagination metadata */
  pagination: PaginationMetadata;
}

/**
 * Response for POST /queries/{id}/execute
 */
export interface ExecuteQueryResponse {
  /** Query attempt ID */
  id: number;
  /** Execution status */
  status: QueryStatus;
  /** When executed */
  executed_at: ISO8601Timestamp;
  /** Execution time in milliseconds */
  execution_ms: number;
  /** Query results (null if execution failed) */
  results: QueryResults | null;
  /** Error message if execution failed */
  error_message: string | null;
}

/**
 * Query parameters for GET /queries/{id}/results
 */
export interface QueryResultsParams {
  /** Page number (default: 1) */
  page?: number;
}

/**
 * Response for GET /queries/{id}/results
 */
export interface QueryResultsResponse {
  /** Query attempt ID */
  attempt_id: number;
  /** Total number of rows */
  total_rows: number;
  /** Rows per page (500) */
  page_size: number;
  /** Total number of pages */
  page_count: number;
  /** Current page number */
  current_page: number;
  /** Column names */
  columns: string[];
  /** Result rows for current page */
  rows: Array<Array<any>>;
}

/**
 * Response for POST /queries/{id}/rerun
 */
export interface RerunQueryResponse extends QueryAttempt {
  /** ID of the original query attempt */
  original_attempt_id: number;
}

// ============================================================================
// Admin API
// ============================================================================

/**
 * Response for POST /admin/schema/refresh
 */
export interface RefreshSchemaResponse {
  /** Success message */
  message: string;
  /** Information about new snapshot */
  snapshot: SchemaSnapshot;
}

/**
 * Response for POST /admin/kb/reload
 */
export interface ReloadKBResponse {
  /** Success message */
  message: string;
  /** Reload statistics */
  stats: KBReloadStats;
}

/**
 * Query parameters for GET /admin/metrics
 */
export interface MetricsParams {
  /** Number of weeks to retrieve (default: 4, min: 1, max: 52) */
  weeks?: number;
}

/**
 * Response for GET /admin/metrics
 */
export interface MetricsResponse {
  /** List of metric rows */
  metrics: MetricRow[];
  /** Summary statistics */
  summary: MetricsSummary;
}

// ============================================================================
// System API
// ============================================================================

/**
 * Response for GET /health
 */
export interface HealthCheckResponse {
  /** Overall health status */
  status: string;
  /** Timestamp of health check */
  timestamp: ISO8601Timestamp;
  /** Status of individual services */
  services: ServiceStatus;
}

// ============================================================================
// API Client Types
// ============================================================================

/**
 * Base API error class for typed error handling.
 */
export class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public errorCode?: string
  ) {
    super(detail);
    this.name = "APIError";
  }
}

/**
 * Type guard to check if an error is an APIError.
 */
export function isAPIError(error: unknown): error is APIError {
  return error instanceof APIError;
}

/**
 * Generic API response wrapper for error handling.
 */
export type APIResponse<T> =
  | { success: true; data: T }
  | { success: false; error: APIError };

/**
 * HTTP methods supported by the API.
 */
export type HTTPMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

/**
 * API endpoint configuration.
 */
export interface APIEndpoint {
  /** HTTP method */
  method: HTTPMethod;
  /** URL path (may include path parameters like :id) */
  path: string;
  /** Whether authentication is required */
  requiresAuth: boolean;
  /** Whether admin role is required */
  requiresAdmin?: boolean;
}
