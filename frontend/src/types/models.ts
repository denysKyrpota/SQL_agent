/**
 * Core data model types that represent domain entities.
 * These types are derived from database schema but focused on application use.
 */

import type { ISO8601Date, ISO8601Timestamp, QueryStatus, UserRole } from "./common";

/**
 * User information (excludes sensitive data like password).
 */
export interface User {
  /** User ID */
  id: number;
  /** Username */
  username: string;
  /** User role */
  role: UserRole;
  /** Whether the user account is active */
  active: boolean;
}

/**
 * Session information with token.
 */
export interface SessionInfo {
  /** Session token */
  token: string;
  /** When the session expires */
  expires_at: ISO8601Timestamp;
}

/**
 * Session information without token (for validation responses).
 */
export interface SessionInfoWithoutToken {
  /** When the session expires */
  expires_at: ISO8601Timestamp;
}

/**
 * Query attempt - represents a natural language query and its SQL generation.
 */
export interface QueryAttempt {
  /** Query attempt ID */
  id: number;
  /** Original natural language query from user */
  natural_language_query: string;
  /** Generated SQL (null if generation failed) */
  generated_sql: string | null;
  /** Current status */
  status: QueryStatus;
  /** When the query was created */
  created_at: ISO8601Timestamp;
  /** When SQL generation completed (null if not generated) */
  generated_at: ISO8601Timestamp | null;
  /** Time taken to generate SQL in milliseconds */
  generation_ms: number | null;
  /** Error message if generation or execution failed */
  error_message?: string | null;
}

/**
 * Detailed query attempt with execution information.
 */
export interface QueryAttemptDetail extends QueryAttempt {
  /** When the query was executed (null if not executed) */
  executed_at: ISO8601Timestamp | null;
  /** Time taken to execute query in milliseconds */
  execution_ms: number | null;
  /** ID of original query if this is a re-run */
  original_attempt_id: number | null;
}

/**
 * Simplified query attempt for list views.
 */
export interface SimplifiedQueryAttempt {
  /** Query attempt ID */
  id: number;
  /** Original natural language query */
  natural_language_query: string;
  /** Current status */
  status: QueryStatus;
  /** When created */
  created_at: ISO8601Timestamp;
  /** When executed (null if not executed) */
  executed_at: ISO8601Timestamp | null;
}

/**
 * Query execution results structure.
 */
export interface QueryResults {
  /** Total number of rows in result set */
  total_rows: number;
  /** Number of rows per page */
  page_size: number;
  /** Total number of pages */
  page_count: number;
  /** Column names */
  columns: string[];
  /** Result rows (array of arrays with mixed types) */
  rows: Array<Array<any>>;
}

/**
 * Schema snapshot information.
 */
export interface SchemaSnapshot {
  /** Snapshot ID */
  id: number;
  /** When the schema was loaded */
  loaded_at: ISO8601Timestamp;
  /** Hash of source schema files */
  source_hash: string;
  /** Number of tables */
  table_count: number;
  /** Total number of columns */
  column_count: number;
}

/**
 * Knowledge base reload statistics.
 */
export interface KBReloadStats {
  /** Number of .sql files loaded */
  files_loaded: number;
  /** Number of embeddings generated/updated */
  embeddings_generated: number;
  /** Total load time in milliseconds */
  load_time_ms: number;
}

/**
 * Metrics data row.
 */
export interface MetricRow {
  /** Start of week (ISO date) */
  week_start: ISO8601Date;
  /** User ID (null for aggregated metrics) */
  user_id: number | null;
  /** Username (null for aggregated metrics) */
  username: string | null;
  /** Number of query attempts */
  attempts_count: number;
  /** Number of queries executed */
  executed_count: number;
  /** Number of successful executions */
  success_count: number;
}

/**
 * Metrics summary statistics.
 */
export interface MetricsSummary {
  /** Total query attempts */
  total_attempts: number;
  /** Total queries executed */
  total_executed: number;
  /** Total successful executions */
  total_success: number;
  /** Success rate (0-1) */
  success_rate: number;
  /** Acceptance rate (0-1) */
  acceptance_rate: number;
}

/**
 * Service status information.
 */
export interface ServiceStatus {
  /** SQLite database status */
  database: "up" | "down";
  /** PostgreSQL database status */
  postgresql: "up" | "down";
  /** LLM API status */
  llm_api: "up" | "down";
}
