/**
 * Error message mapping and utilities
 */

import type { ErrorType } from '../types';

/**
 * Map error types to user-friendly messages
 */
export const ERROR_MESSAGES: Record<ErrorType, string> = {
  validation: 'Please check your input and try again',
  generation: 'Unable to generate query. Try rephrasing your question.',
  execution: 'Query failed to execute. The generated SQL may be invalid.',
  timeout: 'Query took too long to execute. Try narrowing your search.',
  network: 'Network error. Please check your internet connection.',
};

/**
 * Get error message for error type
 */
export const getErrorMessage = (type: ErrorType, customMessage?: string): string => {
  return customMessage || ERROR_MESSAGES[type];
};

/**
 * Get recovery suggestion for error type
 */
export const getRecoverySuggestion = (type: ErrorType): string | null => {
  switch (type) {
    case 'generation':
      return 'Try rephrasing your question or being more specific about what you want to query.';
    case 'execution':
      return 'The SQL query may contain errors. You can try regenerating with a different question.';
    case 'timeout':
      return 'Try adding more specific filters or reducing the date range in your question.';
    case 'network':
      return 'Check your internet connection and try again.';
    case 'validation':
      return 'Make sure your question meets the requirements.';
    default:
      return null;
  }
};

/**
 * Check if error is retryable
 */
export const isRetryableError = (type: ErrorType): boolean => {
  return ['generation', 'execution', 'network'].includes(type);
};
