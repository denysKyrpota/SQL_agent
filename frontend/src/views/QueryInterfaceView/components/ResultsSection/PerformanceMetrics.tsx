/**
 * PerformanceMetrics Component
 *
 * Display component showing query performance information including
 * SQL generation time and execution time.
 */

import React from 'react';
import type { PerformanceMetricsProps } from '../../types';
import './PerformanceMetrics.css';

/**
 * Format time value for display
 */
const formatTime = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
};

/**
 * Get performance color based on time
 */
const getPerformanceClass = (ms: number): string => {
  if (ms < 5000) return 'performance-good'; // < 5s
  if (ms < 30000) return 'performance-moderate'; // 5-30s
  return 'performance-slow'; // > 30s
};

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  generationTimeMs,
  executionTimeMs,
  rowCount,
}) => {
  return (
    <div className="performance-metrics">
      {generationTimeMs !== null && (
        <div className="metric">
          <span className="metric-label">Generation:</span>
          <span className={`metric-value ${getPerformanceClass(generationTimeMs)}`}>
            {formatTime(generationTimeMs)}
          </span>
        </div>
      )}

      {executionTimeMs !== null && (
        <div className="metric">
          <span className="metric-label">Execution:</span>
          <span className={`metric-value ${getPerformanceClass(executionTimeMs)}`}>
            {formatTime(executionTimeMs)}
          </span>
        </div>
      )}

      {rowCount !== null && (
        <div className="metric">
          <span className="metric-label">Rows:</span>
          <span className="metric-value">
            {rowCount.toLocaleString()}
          </span>
        </div>
      )}
    </div>
  );
};

export default PerformanceMetrics;
