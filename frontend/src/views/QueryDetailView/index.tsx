/**
 * Query Detail View - Display details of a single query attempt
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQueryAttempt, executeQuery, rerunQuery } from '@/services/queryService';
import Button from '@/components/Button';
import Toast from '@/components/Toast';
import { isAPIError } from '@/types/api';
import type { QueryAttemptDetail } from '@/types/models';
import styles from './QueryDetailView.module.css';

const QueryDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryId = id ? parseInt(id, 10) : null;

  const [query, setQuery] = useState<QueryAttemptDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  useEffect(() => {
    if (!queryId) {
      navigate('/history');
      return;
    }

    const fetchQuery = async () => {
      setIsLoading(true);
      try {
        const data = await getQueryAttempt(queryId);
        setQuery(data);
      } catch (error) {
        console.error('Failed to fetch query:', error);
        const errorMessage = isAPIError(error)
          ? error.detail
          : 'Failed to load query details';
        setToast({ message: errorMessage, type: 'error' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuery();
  }, [queryId, navigate]);

  const handleExecute = async () => {
    if (!queryId) return;

    setIsExecuting(true);
    try {
      const result = await executeQuery(queryId);
      setQuery(prev => prev ? {
        ...prev,
        status: result.status,
        executed_at: result.executed_at,
        execution_ms: result.execution_ms,
        error_message: result.error_message,
      } : null);

      if (result.status === 'success') {
        setToast({ message: 'Query executed successfully!', type: 'success' });
      } else {
        setToast({ message: result.error_message || 'Execution failed', type: 'error' });
      }
    } catch (error) {
      console.error('Failed to execute query:', error);
      const errorMessage = isAPIError(error)
        ? error.detail
        : 'Failed to execute query';
      setToast({ message: errorMessage, type: 'error' });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRerun = async () => {
    if (!queryId) return;

    setIsRerunning(true);
    try {
      const newQuery = await rerunQuery(queryId);
      setToast({ message: 'Query re-run started! Redirecting...', type: 'success' });
      setTimeout(() => {
        navigate(`/query/${newQuery.id}`);
      }, 1000);
    } catch (error) {
      console.error('Failed to re-run query:', error);
      const errorMessage = isAPIError(error)
        ? error.detail
        : 'Failed to re-run query';
      setToast({ message: errorMessage, type: 'error' });
      setIsRerunning(false);
    }
  };

  const handleBack = () => {
    navigate('/history');
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      not_executed: 'Not Executed',
      success: 'Success',
      failed_generation: 'Failed Generation',
      failed_execution: 'Failed Execution',
      timeout: 'Timeout',
    };
    return labels[status] || status;
  };

  const getStatusClass = (status: string) => {
    const classes: Record<string, string> = {
      not_executed: styles['status-pending'],
      success: styles['status-success'],
      failed_generation: styles['status-error'],
      failed_execution: styles['status-error'],
      timeout: styles['status-warning'],
    };
    return classes[status] || '';
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const formatDuration = (ms: number | null) => {
    if (ms === null) return '—';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (isLoading) {
    return (
      <div className={styles['query-detail-view']}>
        <div className={styles['loading-state']}>
          <div className={styles['spinner']} />
          <p>Loading query details...</p>
        </div>
      </div>
    );
  }

  if (!query) {
    return (
      <div className={styles['query-detail-view']}>
        <div className={styles['error-state']}>
          <h2>Query not found</h2>
          <p>The requested query could not be found.</p>
          <Button variant="primary" onClick={handleBack}>
            Back to History
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles['query-detail-view']}>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      )}

      <div className={styles['query-detail-container']}>
        {/* Header */}
        <div className={styles['detail-header']}>
          <button className={styles['back-button']} onClick={handleBack}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back to History
          </button>
          <h1>Query #{query.id}</h1>
        </div>

        {/* Status Badge */}
        <div className={styles['status-section']}>
          <span className={`${styles['status-badge']} ${getStatusClass(query.status)}`}>
            {getStatusLabel(query.status)}
          </span>
          {query.original_attempt_id && (
            <span className={styles['rerun-badge']}>
              Re-run of #{query.original_attempt_id}
            </span>
          )}
        </div>

        {/* Natural Language Query */}
        <section className={styles['detail-section']}>
          <h2>Natural Language Query</h2>
          <div className={styles['query-text']}>
            {query.natural_language_query}
          </div>
        </section>

        {/* Generated SQL */}
        <section className={styles['detail-section']}>
          <h2>Generated SQL</h2>
          {query.generated_sql ? (
            <pre className={styles['sql-block']}>
              <code>{query.generated_sql}</code>
            </pre>
          ) : (
            <p className={styles['no-data']}>No SQL generated</p>
          )}
        </section>

        {/* Timing Information */}
        <section className={styles['detail-section']}>
          <h2>Timing</h2>
          <div className={styles['timing-grid']}>
            <div className={styles['timing-item']}>
              <span className={styles['timing-label']}>Created</span>
              <span className={styles['timing-value']}>{formatDate(query.created_at)}</span>
            </div>
            <div className={styles['timing-item']}>
              <span className={styles['timing-label']}>Generated</span>
              <span className={styles['timing-value']}>
                {query.generated_at ? formatDate(query.generated_at) : '—'}
              </span>
            </div>
            <div className={styles['timing-item']}>
              <span className={styles['timing-label']}>Generation Time</span>
              <span className={styles['timing-value']}>{formatDuration(query.generation_ms)}</span>
            </div>
            <div className={styles['timing-item']}>
              <span className={styles['timing-label']}>Executed</span>
              <span className={styles['timing-value']}>
                {query.executed_at ? formatDate(query.executed_at) : '—'}
              </span>
            </div>
            <div className={styles['timing-item']}>
              <span className={styles['timing-label']}>Execution Time</span>
              <span className={styles['timing-value']}>{formatDuration(query.execution_ms)}</span>
            </div>
          </div>
        </section>

        {/* Error Message */}
        {query.error_message && (
          <section className={styles['detail-section']}>
            <h2>Error</h2>
            <div className={styles['error-block']}>
              {query.error_message}
            </div>
          </section>
        )}

        {/* Actions */}
        <div className={styles['action-buttons']}>
          {query.status === 'not_executed' && query.generated_sql && (
            <Button
              variant="primary"
              onClick={handleExecute}
              disabled={isExecuting || isRerunning}
            >
              {isExecuting ? 'Executing...' : 'Execute Query'}
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={handleRerun}
            disabled={isExecuting || isRerunning}
          >
            {isRerunning ? 'Re-running...' : 'Re-run Query'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default QueryDetailView;
