/**
 * Central export point for all TypeScript types.
 * Import types from this file for convenience.
 */

// Common types
export type {
  ErrorResponse,
  ISO8601Date,
  ISO8601Timestamp,
  MessageResponse,
  PaginatedResponse,
  PaginationMetadata,
  PaginationParams,
  QueryStatus,
  ServiceStatusEnum,
  UserRole,
} from "./common";

// Data models
export type {
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

// API types
export {
  APIError,
  isAPIError,
  type APIEndpoint,
  type APIResponse,
  type CreateQueryRequest,
  type ExecuteQueryResponse,
  type HealthCheckResponse,
  type HTTPMethod,
  type LoginRequest,
  type LoginResponse,
  type LogoutResponse,
  type MetricsParams,
  type MetricsResponse,
  type QueryAttemptDetailResponse,
  type QueryAttemptResponse,
  type QueryListParams,
  type QueryListResponse,
  type QueryResultsParams,
  type QueryResultsResponse,
  type RefreshSchemaResponse,
  type ReloadKBResponse,
  type RerunQueryResponse,
  type SessionResponse,
} from "./api";

// Database types (auto-generated)
export type {
  ID,
  KbExamplesIndex,
  MetricsRollup,
  QueryAttempts,
  QueryResultsManifest,
  SchemaMigrations,
  SchemaSnapshots,
  Sessions,
  Timestamp,
  Users,
} from "./database.types";
