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
import ExampleQuestions from './components/QueryForm/ExampleQuestions';
import Toast from '@/components/Toast';
import ChatPanel from '@/components/ChatPanel';
import {
  executeQuery,
  getQueryResults,
  exportQueryCSV,
  getExampleQuestions,
} from '@/services/queryService';
import chatService from '@/services/chatService';
import { isAPIError } from '@/types/api';
import { getErrorMessage } from './utils/errorMessages';
import styles from './QueryInterfaceView.module.css';

const QueryInterfaceView: React.FC = () => {
  // Example questions from knowledge base
  const [exampleQuestions, setExampleQuestions] = useState<string[]>([]);
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

  // Chat panel state
  const [chatOpen, setChatOpen] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>(undefined);

  // Toast notification state
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  // Load example questions from knowledge base
  useEffect(() => {
    const loadExamples = async () => {
      try {
        const response = await getExampleQuestions();
        const questions = response.examples.map(ex => ex.title);
        setExampleQuestions(questions);
      } catch (error) {
        console.error('Failed to load example questions:', error);
        // Use fallback examples if API fails
        setExampleQuestions([
          "What were our top 10 customers by revenue last quarter?",
          "Show me all orders from the last 30 days",
          "How many active users do we have by region?",
        ]);
      }
    };

    loadExamples();
  }, []);

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

  // Handle query submission - Now uses chat service
  const handleSubmit = async () => {
    // Set loading state first (keep form visible with loading indicator)
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
      // Send message through chat service (creates conversation if needed)
      const response = await chatService.sendMessage({
        content: queryState.naturalLanguageQuery,
        conversation_id: conversationId,
      });

      // Update conversation ID if this is first message
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Enable chat mode after successful generation
      if (!chatOpen) {
        setChatOpen(true);
      }

      // Clear input and saved state
      setQueryState(prev => ({
        ...prev,
        naturalLanguageQuery: '',
        isGenerating: false,
        loadingStage: null,
      }));
      sessionStorage.removeItem('queryInputText');

      // The ChatPanel will automatically reload and show the new messages

    } catch (error) {
      console.error('Query submission error:', error);

      // Switch to chat mode even on error so user can see error and retry
      if (!chatOpen) {
        setChatOpen(true);
      }

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

  // Handle example question selection
  const handleExampleSelect = (example: string) => {
    handleInputChange(example);
  };

  // Handle query execution from chat
  const handleChatQueryExecute = async (queryAttemptId: number) => {
    setQueryState(prev => ({
      ...prev,
      queryId: queryAttemptId,
      isExecuting: true,
      loadingStage: 'execution',
      error: null,
    }));

    try {
      const response = await executeQuery(queryAttemptId);

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

  // Determine what to show
  const showExampleQuestions = !chatOpen;
  const isInitialState = !chatOpen;

  return (
    <main className={styles['query-interface']} aria-label="Query Interface">
      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      )}

      <div className={styles['query-interface-container']}>
        {/* Hero Section - Title */}
        <div className={(styles as any)['hero-section']}>
          <h1>Ask Your Database</h1>

          {/* Query Form - Centered when in initial state */}
          {isInitialState && (
            <div className={(styles as any)['centered-form']}>
              <div className={styles['query-form']}>
                <QueryForm
                  value={queryState.naturalLanguageQuery}
                  onChange={handleInputChange}
                  onSubmit={handleSubmit}
                  disabled={queryState.isGenerating || queryState.isExecuting}
                />
              </div>
              {/* Loading Indicator for initial form state */}
              {queryState.loadingStage && (
                <LoadingIndicator stage={queryState.loadingStage} />
              )}
            </div>
          )}
        </div>

        {/* Layout Container - Shows when in chat mode */}
        <div className={(styles as any)['layout-container']}>
          {/* Main Content (Center) */}
          <div className={(styles as any)['main-content']}>
            {/* Chat Mode - Show chat panel and other content */}
            {chatOpen && (
              <>
                {/* Chat Panel */}
                <div className={(styles as any)['chat-panel-container']}>
                  <ChatPanel
                    conversationId={conversationId}
                    onQueryExecute={handleChatQueryExecute}
                    onConversationChange={setConversationId}
                    className={(styles as any)['chat-panel']}
                  />
                </div>

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
              </>
            )}
          </div>

          {/* Sidebar (Right) - Example Questions */}
          {showExampleQuestions && (
            <aside className={(styles as any)['sidebar']}>
              <div className={(styles as any)['sidebar-panel']}>
                <ExampleQuestions
                  examples={exampleQuestions}
                  onSelect={handleExampleSelect}
                  disabled={queryState.isGenerating || queryState.isExecuting}
                />
              </div>
            </aside>
          )}
        </div>
      </div>
    </main>
  );
};

export default QueryInterfaceView;
