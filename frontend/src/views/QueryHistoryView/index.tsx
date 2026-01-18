/**
 * Query History View - Display and manage past queries
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { listQueries, rerunQuery } from '@/services/queryService';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/Button';
import Pagination from '@/components/Pagination';
import Toast from '@/components/Toast';
import QueryFilters from './components/QueryFilters';
import QueryHistoryTable from './components/QueryHistoryTable';
import { isAPIError } from '@/types/api';
import type { SimplifiedQueryAttempt, QueryStatus } from '@/types/models';
import styles from './QueryHistoryView.module.css';

const QueryHistoryView: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // State
  const [queries, setQueries] = useState<SimplifiedQueryAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<QueryStatus | 'all'>('all');
  const [isRerunning, setIsRerunning] = useState<number | null>(null);

  // Toast notification
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  /**
   * Fetch queries from API
   */
  const fetchQueries = useCallback(async () => {
    setIsLoading(true);

    try {
      const params: any = {
        page: currentPage,
        limit: 20,
      };

      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      const response = await listQueries(params);

      setQueries(response.queries);
      setTotalPages(response.pagination.page_count);
    } catch (error) {
      console.error('Failed to fetch queries:', error);

      const errorMessage = isAPIError(error)
        ? error.detail
        : 'Failed to load query history';

      setToast({
        message: errorMessage,
        type: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, statusFilter]);

  /**
   * Load queries on mount and when filters change
   */
  useEffect(() => {
    fetchQueries();
  }, [fetchQueries]);

  /**
   * Handle status filter change
   */
  const handleFilterChange = (status: QueryStatus | 'all') => {
    setStatusFilter(status);
    setCurrentPage(1); // Reset to first page
  };

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  /**
   * Handle re-run query
   */
  const handleRerun = async (queryId: number) => {
    setIsRerunning(queryId);

    try {
      const newQuery = await rerunQuery(queryId);

      setToast({
        message: 'Query re-run started! Redirecting...',
        type: 'success',
      });

      // Redirect to main query interface with the new query
      setTimeout(() => {
        navigate(`/?queryId=${newQuery.id}`);
      }, 1000);
    } catch (error) {
      console.error('Failed to re-run query:', error);

      const errorMessage = isAPIError(error)
        ? error.detail
        : 'Failed to re-run query';

      setToast({
        message: errorMessage,
        type: 'error',
      });

      setIsRerunning(null);
    }
  };

  /**
   * Handle view query details
   */
  const handleViewDetails = (queryId: number) => {
    navigate(`/query/${queryId}`);
  };

  /**
   * Handle new query click
   */
  const handleNewQuery = () => {
    navigate('/');
  };

  return (
    <div className={styles['query-history-view']}>
      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      )}

      <div className={styles['query-history-container']}>
        {/* Header */}
        <div className={styles['query-history-header']}>
          <div>
            <h1>Query History</h1>
            <p className={styles['subtitle']}>
              View and manage your past queries
              {user?.role === 'admin' && ' (all users)'}
            </p>
          </div>

          <Button variant="primary" onClick={handleNewQuery}>
            + New Query
          </Button>
        </div>

        {/* Filters */}
        <QueryFilters
          currentFilter={statusFilter}
          onFilterChange={handleFilterChange}
        />

        {/* Loading State */}
        {isLoading && (
          <div className={styles['loading-state']}>
            <div className={styles['spinner']} />
            <p>Loading queries...</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && queries.length === 0 && (
          <div className={styles['empty-state']}>
            <div className={styles['empty-icon']}>📋</div>
            <h2>No queries found</h2>
            <p>
              {statusFilter === 'all'
                ? "You haven't submitted any queries yet."
                : `No queries with status "${statusFilter}".`}
            </p>
            <Button variant="primary" onClick={handleNewQuery}>
              Create Your First Query
            </Button>
          </div>
        )}

        {/* Query Table */}
        {!isLoading && queries.length > 0 && (
          <>
            <QueryHistoryTable
              queries={queries}
              onRerun={handleRerun}
              onViewDetails={handleViewDetails}
              rerunningId={isRerunning}
            />

            {/* Pagination */}
            {totalPages > 1 && (
              <div className={styles['pagination-container']}>
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        )}

        {/* Stats Footer */}
        {!isLoading && queries.length > 0 && (
          <div className={styles['stats-footer']}>
            <p>
              Showing <strong>{queries.length}</strong> queries on page{' '}
              <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueryHistoryView;
