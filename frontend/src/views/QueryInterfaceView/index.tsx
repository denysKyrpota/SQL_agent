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
    // TODO: Implement in next step
    console.log('Submit query:', queryState.naturalLanguageQuery);
  };

  // Handle SQL execution
  const handleExecute = async () => {
    // TODO: Implement in next step
    console.log('Execute query:', queryState.queryId);
  };

  // Handle copy SQL to clipboard
  const handleCopy = async () => {
    // TODO: Implement in next step
    console.log('Copy SQL');
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    // TODO: Implement in next step
    console.log('Change page:', page);
  };

  // Handle CSV export
  const handleExport = async () => {
    // TODO: Implement in next step
    console.log('Export CSV');
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
