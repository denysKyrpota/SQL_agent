/**
 * Type utilities and type guards for runtime type checking.
 */

import type { QueryStatus, UserRole } from "./common";

/**
 * Type guard to check if a string is a valid QueryStatus.
 */
export function isQueryStatus(value: unknown): value is QueryStatus {
  return (
    typeof value === "string" &&
    [
      "not_executed",
      "failed_generation",
      "failed_execution",
      "success",
      "timeout",
    ].includes(value)
  );
}

/**
 * Type guard to check if a string is a valid UserRole.
 */
export function isUserRole(value: unknown): value is UserRole {
  return typeof value === "string" && ["admin", "user"].includes(value);
}

/**
 * Type guard to check if a value is a valid ISO 8601 timestamp string.
 */
export function isISO8601Timestamp(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$/;
  return isoRegex.test(value);
}

/**
 * Type guard to check if a value is a valid ISO 8601 date string.
 */
export function isISO8601Date(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  return dateRegex.test(value);
}

/**
 * Safely parse an ISO 8601 timestamp to a Date object.
 * Returns null if parsing fails.
 */
export function parseISO8601(timestamp: string | null | undefined): Date | null {
  if (!timestamp) return null;
  try {
    const date = new Date(timestamp);
    return isNaN(date.getTime()) ? null : date;
  } catch {
    return null;
  }
}

/**
 * Format a Date object to ISO 8601 timestamp string.
 */
export function toISO8601(date: Date): string {
  return date.toISOString();
}

/**
 * Check if a timestamp is in the past.
 */
export function isExpired(timestamp: string | null | undefined): boolean {
  const date = parseISO8601(timestamp);
  if (!date) return true;
  return date.getTime() < Date.now();
}

/**
 * Get a human-readable relative time string (e.g., "2 minutes ago").
 */
export function getRelativeTime(timestamp: string | null | undefined): string {
  const date = parseISO8601(timestamp);
  if (!date) return "Unknown";

  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds} second${seconds !== 1 ? "s" : ""} ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? "s" : ""} ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days !== 1 ? "s" : ""} ago`;

  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months !== 1 ? "s" : ""} ago`;

  const years = Math.floor(months / 12);
  return `${years} year${years !== 1 ? "s" : ""} ago`;
}

/**
 * Format milliseconds to a human-readable duration.
 * @param ms - Duration in milliseconds
 * @returns Formatted string (e.g., "2.5s", "150ms")
 */
export function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return "N/A";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

/**
 * Get a user-friendly status label for query status.
 */
export function getStatusLabel(status: QueryStatus): string {
  const labels: Record<QueryStatus, string> = {
    not_executed: "Not Executed",
    failed_generation: "Generation Failed",
    failed_execution: "Execution Failed",
    success: "Success",
    timeout: "Timeout",
  };
  return labels[status] || status;
}

/**
 * Get a CSS class name for query status styling.
 */
export function getStatusClassName(status: QueryStatus): string {
  const classNames: Record<QueryStatus, string> = {
    not_executed: "status-pending",
    failed_generation: "status-error",
    failed_execution: "status-error",
    success: "status-success",
    timeout: "status-warning",
  };
  return classNames[status] || "status-default";
}

/**
 * Format a success/acceptance rate as percentage.
 * @param rate - Rate between 0 and 1
 * @param decimals - Number of decimal places (default: 1)
 */
export function formatRate(rate: number, decimals: number = 1): string {
  return `${(rate * 100).toFixed(decimals)}%`;
}

/**
 * Deep clone an object (for immutable updates).
 * Note: This is a simple implementation. For complex objects, consider using a library.
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Type-safe object keys helper.
 */
export function typedKeys<T extends object>(obj: T): Array<keyof T> {
  return Object.keys(obj) as Array<keyof T>;
}

/**
 * Safely access nested properties with null/undefined checking.
 */
export function safeAccess<T, K extends keyof T>(
  obj: T | null | undefined,
  key: K
): T[K] | undefined {
  return obj?.[key];
}
