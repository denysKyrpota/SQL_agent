/**
 * Type definitions for Query Interface View
 */

import type { QueryStatus, ISO8601Timestamp } from '@/types/common';
import type { QueryResults } from '@/types/models';

/**
 * Loading stage enum for multi-stage generation
 */
export type LoadingStage = 'schema' | 'generation' | 'execution';

/**
 * Error type enum
 */
export type ErrorType =
  | 'validation'
  | 'generation'
  | 'execution'
  | 'timeout'
  | 'network';

/**
 * Query error structure
 */
export interface QueryError {
  type: ErrorType;
  message: string;
  detail?: string | null;
}

/**
 * Main state interface for Query Interface View
 */
export interface QueryInterfaceState {
  // Input state
  naturalLanguageQuery: string;

  // Query attempt state
  queryId: number | null;
  generatedSql: string | null;
  status: QueryStatus;

  // Timing
  generationTimeMs: number | null;
  executionTimeMs: number | null;

  // Results state
  results: QueryResults | null;
  currentPage: number;

  // Error state
  error: QueryError | null;

  // UI state
  isGenerating: boolean;
  isExecuting: boolean;
  loadingStage: LoadingStage | null;
}

/**
 * Example questions configuration
 */
export interface ExampleQuestion {
  text: string;
  category?: string;
}

/**
 * Props for QueryForm component
 */
export interface QueryFormProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  examples: string[];
}

/**
 * Props for TextArea component
 */
export interface TextAreaProps {
  value: string;
  onChange: (value: string) => void;
  maxLength: number;
  placeholder: string;
  disabled: boolean;
  autoFocus?: boolean;
  label: string;
  id: string;
}

/**
 * Props for CharacterCount component
 */
export interface CharacterCountProps {
  current: number;
  max: number;
}

/**
 * Props for ExampleQuestions component
 */
export interface ExampleQuestionsProps {
  examples: string[];
  onSelect: (example: string) => void;
  disabled: boolean;
}

/**
 * Props for LoadingIndicator component
 */
export interface LoadingIndicatorProps {
  stage: LoadingStage;
  startTime?: Date;
}

/**
 * Props for SqlPreviewSection component
 */
export interface SqlPreviewSectionProps {
  sql: string;
  onExecute: () => void;
  onCopy: () => void;
  executing: boolean;
}

/**
 * Props for SqlPreview component
 */
export interface SqlPreviewProps {
  sql: string;
  showLineNumbers?: boolean;
  language?: string;
}

/**
 * Props for ErrorAlert component
 */
export interface ErrorAlertProps {
  type: ErrorType;
  message: string;
  detail?: string | null;
  dismissible?: boolean;
  onDismiss?: () => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Props for ResultsSection component
 */
export interface ResultsSectionProps {
  results: QueryResults;
  currentPage: number;
  onPageChange: (page: number) => void;
  onExport: () => void;
  generationTimeMs: number;
  executionTimeMs: number;
}

/**
 * Props for PerformanceMetrics component
 */
export interface PerformanceMetricsProps {
  generationTimeMs: number | null;
  executionTimeMs: number | null;
  rowCount: number | null;
}

/**
 * Props for ResultsTable component
 */
export interface ResultsTableProps {
  columns: string[];
  rows: Array<Array<any>>;
  totalRows: number;
}

/**
 * Props for Pagination component
 */
export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalRows: number;
  onPageChange: (page: number) => void;
}

/**
 * Button variant types
 */
export type ButtonVariant = 'primary' | 'secondary' | 'danger';

/**
 * Button size types
 */
export type ButtonSize = 'small' | 'medium' | 'large';

/**
 * Props for Button component
 */
export interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit';
  icon?: React.ReactNode;
  fullWidth?: boolean;
  ariaLabel?: string;
}
