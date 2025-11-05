/**
 * Query Interface View - Main view component
 *
 * Primary workspace for submitting natural language questions and executing SQL queries.
 * Handles the complete query workflow from input through SQL generation, preview, execution,
 * and results display.
 */

import React, { useState, useEffect } from 'react';
import type { QueryInterfaceState } from './types';
import QueryForm from './components/QueryForm';
import LoadingIndicator from './components/LoadingIndicator';
import SqlPreviewSection from './components/SqlPreviewSection';
import ErrorAlert from './components/ErrorAlert';
import ResultsSection from './components/ResultsSection';
import Toast from '@/components/Toast';
import { createQuery, executeQuery, getQueryResults, exportQueryCSV } from '@/services/queryService';
import { APIError, isAPIError } from '@/types/api';
import { getErrorMessage } from './utils/errorMessages';
import './QueryInterfaceView.module.css';

/**
 * Example questions to guide users
 */
const EXAMPLE_QUESTIONS = [
  "What were our top 10 customers by revenue last quarter?",
  "Show me all orders from the last 30 days",
  "How many active users do we have by region?",
  "What are the best-selling products this month?",
  "List all customers who haven't ordered in 90 days"
];

const QueryInterfaceView: React.FC = () => {
  // Main state
  const [queryState, setQueryState] = useState<QueryInterfaceState>({
    naturalLanguageQuery: '',
    queryId: null,
    generatedSql: null,
    status: 'not_executed',
    generationTimeMs: null,
    executionTimeMs: null,
    results: null,
    currentPage: 1,
    error: null,
    isGenerating: false,
    isExecuting: false,
    loadingStage: null,
  });

  // Toast notification state
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  // Restore saved input on mount
  useEffect(() => {
    const savedInput = sessionStorage.getItem('queryInputText');
    if (savedInput) {
      setQueryState(prev => ({ ...prev, naturalLanguageQuery: savedInput }));
    }
  }, []);

  // Save input to sessionStorage on change
  const handleInputChange = (value: string) => {
    setQueryState(prev => ({ ...prev, naturalLanguageQuery: value }));
    sessionStorage.setItem('queryInputText', value);
  };

  // Handle query submission
  const handleSubmit = async () => {
    // Clear previous state
    setQueryState(prev => ({
      ...prev,
      error: null,
      generatedSql: null,
      results: null,
      queryId: null,
      isGenerating: true,
      loadingStage: 'schema',
    }));

    try {
      // Stage 1: Schema analysis (simulated, happens on backend)
      await new Promise(resolve => setTimeout(resolve, 500));

      setQueryState(prev => ({ ...prev, loadingStage: 'generation' }));

      // Call API to create query and generate SQL
      const response = await createQuery(queryState.naturalLanguageQuery);

      // Check if generation was successful
      if (response.status === 'failed_generation') {
        setQueryState(prev => ({
          ...prev,
          isGenerating: false,
          loadingStage: null,
          error: {
            type: 'generation',
            message: getErrorMessage('generation'),
            detail: response.error_message || undefined,
          },
        }));
        return;
      }

      // Success - SQL generated
      setQueryState(prev => ({
        ...prev,
        isGenerating: false,
        loadingStage: null,
        queryId: response.id,
        generatedSql: response.generated_sql,
        status: response.status,
        generationTimeMs: response.generation_ms,
      }));

      // Clear saved input on success
      sessionStorage.removeItem('queryInputText');

      // Auto-scroll to SQL preview
      setTimeout(() => {
        const sqlSection = document.querySelector('.sql-preview-section');
        sqlSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (error) {
      console.error('Query submission error:', error);

      let errorType: 'generation' | 'network' = 'generation';
      let errorMessage = 'An unexpected error occurred';
      let errorDetail: string | undefined;

      if (isAPIError(error)) {
        if (error.status === 503) {
          errorMessage = 'Service temporarily unavailable. Please try again.';
          errorType = 'network';
        } else if (error.status === 429) {
          errorMessage = 'Too many requests. Please wait a moment and try again.';
          errorType = 'network';
        } else if (error.errorCode === 'NETWORK_ERROR') {
          errorType = 'network';
          errorMessage = error.detail;
        } else {
          errorDetail = error.detail;
        }
      }

      setQueryState(prev => ({
        ...prev,
        isGenerating: false,
        loadingStage: null,
        error: {
          type: errorType,
          message: errorMessage,
          detail: errorDetail,
        },
      }));
    }
  };

  // Handle SQL execution
  const handleExecute = async () => {
    if (!queryState.queryId) return;

    setQueryState(prev => ({
      ...prev,
      isExecuting: true,
      loadingStage: 'execution',
      error: null,
    }));

    try {
      const response = await executeQuery(queryState.queryId);

      // Check execution status
      if (response.status === 'failed_execution') {
        setQueryState(prev => ({
          ...prev,
          isExecuting: false,
          loadingStage: null,
          error: {
            type: 'execution',
            message: getErrorMessage('execution'),
            detail: response.error_message || undefined,
          },
        }));
        return;
      }

      if (response.status === 'timeout') {
        setQueryState(prev => ({
          ...prev,
          isExecuting: false,
          loadingStage: null,
          error: {
            type: 'timeout',
            message: getErrorMessage('timeout'),
            detail: response.error_message || undefined,
          },
        }));
        return;
      }

      // Success
      setQueryState(prev => ({
        ...prev,
        isExecuting: false,
        loadingStage: null,
        status: response.status,
        executionTimeMs: response.execution_ms,
        results: response.results,
        currentPage: 1,
      }));

      // Auto-scroll to results
      setTimeout(() => {
        const resultsSection = document.querySelector('.results-section');
        resultsSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (error) {
      console.error('Query execution error:', error);

      let errorType: 'execution' | 'timeout' | 'network' = 'execution';
      let errorMessage = 'An unexpected error occurred during execution';
      let errorDetail: string | undefined;

      if (isAPIError(error)) {
        if (error.status === 408 || error.errorCode === 'TIMEOUT') {
          errorType = 'timeout';
          errorMessage = getErrorMessage('timeout');
        } else if (error.errorCode === 'NETWORK_ERROR') {
          errorType = 'network';
          errorMessage = error.detail;
        } else {
          errorDetail = error.detail;
        }
      }

      setQueryState(prev => ({
        ...prev,
        isExecuting: false,
        loadingStage: null,
        error: {
          type: errorType,
          message: errorMessage,
          detail: errorDetail,
        },
      }));
    }
  };

  // Handle copy SQL to clipboard
  const handleCopy = async () => {
    if (!queryState.generatedSql) return;

    try {
      await navigator.clipboard.writeText(queryState.generatedSql);
      setToast({
        message: 'SQL copied to clipboard!',
        type: 'success',
      });
    } catch (error) {
      setToast({
        message: 'Failed to copy SQL',
        type: 'error',
      });
    }
  };

  // Handle page change
  const handlePageChange = async (page: number) => {
    if (!queryState.queryId) return;

    try {
      const response = await getQueryResults(queryState.queryId, { page });

      setQueryState(prev => ({
        ...prev,
        results: {
          total_rows: response.total_rows,
          page_size: response.page_size,
          page_count: response.page_count,
          columns: response.columns,
          rows: response.rows,
        },
        currentPage: response.current_page,
      }));

      // Scroll to top of results
      setTimeout(() => {
        const resultsSection = document.querySelector('.results-section');
        resultsSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (error) {
      console.error('Page change error:', error);

      setToast({
        message: 'Failed to load page. Please try again.',
        type: 'error',
      });
    }
  };

  // Handle CSV export
  const handleExport = async () => {
    if (!queryState.queryId) return;

    try {
      await exportQueryCSV(queryState.queryId);

      setToast({
        message: 'CSV exported successfully!',
        type: 'success',
      });
    } catch (error) {
      console.error('Export error:', error);

      let errorMessage = 'Failed to export CSV. Please try again.';

      if (isAPIError(error)) {
        if (error.status === 413) {
          errorMessage = 'Results are too large to export (max 10,000 rows).';
        } else {
          errorMessage = error.detail;
        }
      }

      setToast({
        message: errorMessage,
        type: 'error',
      });
    }
  };

  // Handle retry after error
  const handleRetry = () => {
    setQueryState(prev => ({
      ...prev,
      error: null,
      generatedSql: null,
      results: null,
      queryId: null,
      status: 'not_executed',
    }));
  };

  return (
    <main className="query-interface" aria-label="Query Interface">
      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      )}

      <div className="query-interface-container">
        <h1>Ask Your Database</h1>

        {/* Query Form Section */}
        <QueryForm
          value={queryState.naturalLanguageQuery}
          onChange={handleInputChange}
          onSubmit={handleSubmit}
          disabled={queryState.isGenerating || queryState.isExecuting}
          examples={EXAMPLE_QUESTIONS}
        />

        {/* Loading Indicator */}
        {queryState.loadingStage && (
          <LoadingIndicator stage={queryState.loadingStage} />
        )}

        {/* Error Alert */}
        {queryState.error && (
          <ErrorAlert
            type={queryState.error.type}
            message={queryState.error.message}
            detail={queryState.error.detail}
            dismissible={true}
            onDismiss={handleRetry}
            action={{
              label: 'Try Again',
              onClick: handleRetry,
            }}
          />
        )}

        {/* SQL Preview Section */}
        {queryState.generatedSql && !queryState.error && (
          <SqlPreviewSection
            sql={queryState.generatedSql}
            onExecute={handleExecute}
            onCopy={handleCopy}
            executing={queryState.isExecuting}
          />
        )}

        {/* Results Section */}
        {queryState.results && queryState.status === 'success' && (
          <ResultsSection
            results={queryState.results}
            currentPage={queryState.currentPage}
            onPageChange={handlePageChange}
            onExport={handleExport}
            generationTimeMs={queryState.generationTimeMs || 0}
            executionTimeMs={queryState.executionTimeMs || 0}
          />
        )}
      </div>
    </main>
  );
};

export default QueryInterfaceView;
