/**
 * Common types and enums used across the application.
 * These types mirror the backend Pydantic schemas.
 */

/**
 * Query attempt status types.
 */
export type QueryStatus =
  | "not_executed"
  | "failed_generation"
  | "failed_execution"
  | "success"
  | "timeout";

/**
 * User role types.
 */
export type UserRole = "admin" | "user";

/**
 * Service status enum.
 */
export type ServiceStatusEnum = "up" | "down";

/**
 * Timestamp string in ISO 8601 format.
 * Example: "2025-10-28T12:00:00Z"
 */
export type ISO8601Timestamp = string;

/**
 * ISO 8601 date string (YYYY-MM-DD).
 * Example: "2025-10-28"
 */
export type ISO8601Date = string;

/**
 * Pagination metadata for list responses.
 */
export interface PaginationMetadata {
  /** Current page number (1-indexed) */
  page: number;
  /** Number of items per page */
  page_size: number;
  /** Total number of items across all pages */
  total_count: number;
  /** Total number of pages */
  total_pages: number;
}

/**
 * Query parameters for pagination.
 */
export interface PaginationParams {
  /** Page number (default: 1, min: 1) */
  page?: number;
  /** Items per page (default: 20, min: 1, max: 100) */
  page_size?: number;
}

/**
 * Standard error response structure.
 */
export interface ErrorResponse {
  /** Human-readable error message */
  detail: string;
  /** Machine-readable error code (optional) */
  error_code?: string | null;
}

/**
 * Simple message response.
 */
export interface MessageResponse {
  /** Response message */
  message: string;
}

/**
 * Generic paginated response wrapper.
 * @template T - Type of items in the response
 */
export interface PaginatedResponse<T> {
  /** Array of items for current page */
  items: T[];
  /** Pagination metadata */
  pagination: PaginationMetadata;
}
