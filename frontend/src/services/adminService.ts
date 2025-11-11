/**
 * Admin Service - API calls for admin-only endpoints
 */

import apiClient from './apiClient';
import type {
  RefreshSchemaResponse,
  ReloadKBResponse,
  MetricsResponse,
  MetricsParams,
} from '@/types/api';

/**
 * Refresh PostgreSQL schema snapshot
 * POST /admin/schema/refresh
 */
export async function refreshSchema(): Promise<RefreshSchemaResponse> {
  return apiClient.post<RefreshSchemaResponse>('/admin/schema/refresh');
}

/**
 * Reload knowledge base examples from files
 * POST /admin/kb/reload
 */
export async function reloadKnowledgeBase(): Promise<ReloadKBResponse> {
  return apiClient.post<ReloadKBResponse>('/admin/kb/reload');
}

/**
 * Get system metrics (admin only)
 * GET /admin/metrics
 */
export async function getMetrics(
  params: MetricsParams = {}
): Promise<MetricsResponse> {
  const queryParams = new URLSearchParams();

  if (params.weeks) {
    queryParams.append('weeks', params.weeks.toString());
  }

  const queryString = queryParams.toString();
  const endpoint = `/admin/metrics${queryString ? `?${queryString}` : ''}`;

  return apiClient.get<MetricsResponse>(endpoint);
}
