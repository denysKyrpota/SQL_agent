/**
 * Query History Table - Displays list of past queries in table format
 */

import React from 'react';
import Button from '@/components/Button';
import type { SimplifiedQueryAttempt } from '@/types/models';
import { formatDate, formatTimeAgo } from '../utils/dateUtils';
import { getStatusBadge } from '../utils/statusUtils';
import './QueryHistoryTable.module.css';

interface QueryHistoryTableProps {
  queries: SimplifiedQueryAttempt[];
  onRerun: (queryId: number) => void;
  onViewDetails: (queryId: number) => void;
  rerunningId: number | null;
}

const QueryHistoryTable: React.FC<QueryHistoryTableProps> = ({
  queries,
  onRerun,
  onViewDetails,
  rerunningId,
}) => {
  return (
    <div className="query-history-table-container">
      <table className="query-history-table">
        <thead>
          <tr>
            <th>Query</th>
            <th>Status</th>
            <th>Submitted</th>
            <th>Results</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {queries.map((query) => (
            <tr key={query.id}>
              {/* Query Text */}
              <td className="query-text-cell">
                <div className="query-text" title={query.natural_language_query}>
                  {query.natural_language_query}
                </div>
                <div className="query-meta">
                  ID: {query.id} • User: {query.user_id}
                </div>
              </td>

              {/* Status */}
              <td className="status-cell">
                {getStatusBadge(query.status)}
              </td>

              {/* Submitted Date */}
              <td className="date-cell">
                <div className="date-primary">
                  {formatTimeAgo(query.submitted_at)}
                </div>
                <div className="date-secondary">
                  {formatDate(query.submitted_at)}
                </div>
              </td>

              {/* Results */}
              <td className="results-cell">
                {query.status === 'success' && query.row_count !== null ? (
                  <div className="results-info">
                    <strong>{query.row_count.toLocaleString()}</strong> rows
                  </div>
                ) : (
                  <span className="no-results">—</span>
                )}
              </td>

              {/* Actions */}
              <td className="actions-cell">
                <div className="action-buttons">
                  <Button
                    variant="secondary"
                    size="small"
                    onClick={() => onViewDetails(query.id)}
                  >
                    View
                  </Button>

                  <Button
                    variant="secondary"
                    size="small"
                    onClick={() => onRerun(query.id)}
                    disabled={rerunningId !== null}
                  >
                    {rerunningId === query.id ? 'Re-running...' : 'Re-run'}
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default QueryHistoryTable;
