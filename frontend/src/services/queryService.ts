/**
 * Query Service - API calls for query workflow
 */

import apiClient from './apiClient';
import type {
  CreateQueryRequest,
  QueryAttemptResponse,
  QueryAttemptDetailResponse,
  ExecuteQueryResponse,
  QueryResultsResponse,
  QueryResultsParams,
} from '@/types/api';

/**
 * Submit natural language query and generate SQL
 * POST /queries
 */
export async function createQuery(
  naturalLanguageQuery: string
): Promise<QueryAttemptResponse> {
  const request: CreateQueryRequest = {
    natural_language_query: naturalLanguageQuery,
  };

  return apiClient.post<QueryAttemptResponse>('/queries', request);
}

/**
 * Get query attempt details
 * GET /queries/{id}
 */
export async function getQueryAttempt(
  queryId: number
): Promise<QueryAttemptDetailResponse> {
  return apiClient.get<QueryAttemptDetailResponse>(`/queries/${queryId}`);
}

/**
 * Execute generated SQL
 * POST /queries/{id}/execute
 */
export async function executeQuery(
  queryId: number
): Promise<ExecuteQueryResponse> {
  return apiClient.post<ExecuteQueryResponse>(
    `/queries/${queryId}/execute`,
    undefined,
    { timeout: 300000 } // 5 minute timeout for query execution
  );
}

/**
 * Get paginated query results
 * GET /queries/{id}/results
 */
export async function getQueryResults(
  queryId: number,
  params: QueryResultsParams = {}
): Promise<QueryResultsResponse> {
  const queryParams = new URLSearchParams();

  if (params.page) {
    queryParams.append('page', params.page.toString());
  }

  const queryString = queryParams.toString();
  const endpoint = `/queries/${queryId}/results${queryString ? `?${queryString}` : ''}`;

  return apiClient.get<QueryResultsResponse>(endpoint);
}

/**
 * Export query results as CSV
 * GET /queries/{id}/export
 */
export async function exportQueryCSV(queryId: number): Promise<void> {
  const blob = await apiClient.download(`/queries/${queryId}/export`);

  // Create download link
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `query_${queryId}_${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();

  // Cleanup
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/**
 * Re-run a historical query
 * POST /queries/{id}/rerun
 */
export async function rerunQuery(
  queryId: number
): Promise<QueryAttemptResponse> {
  return apiClient.post<QueryAttemptResponse>(`/queries/${queryId}/rerun`);
}
