/**
 * Query History Table - Displays list of past queries in table format
 */

import React from 'react';
import Button from '@/components/Button';
import type { SimplifiedQueryAttempt } from '@/types/models';
import { formatDate, formatTimeAgo } from '../utils/dateUtils';
import { getStatusBadge } from '../utils/statusUtils';
import styles from './QueryHistoryTable.module.css';

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
    <div className={styles['query-history-table-container']}>
      <table className={styles['query-history-table']}>
        <thead>
          <tr>
            <th>Query</th>
            <th>Status</th>
            <th>Created</th>
            <th>Executed</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {queries.map((query) => (
            <tr key={query.id}>
              {/* Query Text */}
              <td className={styles['query-text-cell']}>
                <div className={styles['query-text']} title={query.natural_language_query}>
                  {query.natural_language_query}
                </div>
                <div className={styles['query-meta']}>
                  ID: {query.id}
                </div>
              </td>

              {/* Status */}
              <td className={styles['status-cell']}>
                {getStatusBadge(query.status)}
              </td>

              {/* Created Date */}
              <td className={styles['date-cell']}>
                <div className={styles['date-primary']}>
                  {formatTimeAgo(query.created_at)}
                </div>
                <div className={styles['date-secondary']}>
                  {formatDate(query.created_at)}
                </div>
              </td>

              {/* Executed Date */}
              <td className={styles['date-cell']}>
                {query.executed_at ? (
                  <>
                    <div className={styles['date-primary']}>
                      {formatTimeAgo(query.executed_at)}
                    </div>
                    <div className={styles['date-secondary']}>
                      {formatDate(query.executed_at)}
                    </div>
                  </>
                ) : (
                  <span className={styles['no-results']}>—</span>
                )}
              </td>

              {/* Actions */}
              <td className={styles['actions-cell']}>
                <div className={styles['action-buttons']}>
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
