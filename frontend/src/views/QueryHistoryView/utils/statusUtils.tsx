/**
 * Status badge utilities
 */

import React from 'react';
import type { QueryStatus } from '@/types/common';

/**
 * Get status badge component with appropriate styling
 */
export function getStatusBadge(status: QueryStatus): React.ReactNode {
  const statusConfig: Record<
    QueryStatus,
    { label: string; className: string; icon: string }
  > = {
    not_executed: {
      label: 'Not Executed',
      className: 'status-badge status-not-executed',
      icon: '⏸️',
    },
    success: {
      label: 'Success',
      className: 'status-badge status-success',
      icon: '✅',
    },
    failed_generation: {
      label: 'Failed Generation',
      className: 'status-badge status-failed',
      icon: '❌',
    },
    failed_execution: {
      label: 'Failed Execution',
      className: 'status-badge status-failed',
      icon: '❌',
    },
    timeout: {
      label: 'Timeout',
      className: 'status-badge status-timeout',
      icon: '⏱️',
    },
  };

  const config = statusConfig[status];

  return (
    <span className={config.className} title={config.label}>
      <span className="status-icon">{config.icon}</span>
      <span className="status-label">{config.label}</span>
    </span>
  );
}

/**
 * Get status color for charts/graphs
 */
export function getStatusColor(status: QueryStatus): string {
  const colors: Record<QueryStatus, string> = {
    not_executed: '#718096',
    success: '#48bb78',
    failed_generation: '#f56565',
    failed_execution: '#f56565',
    timeout: '#ed8936',
  };

  return colors[status] || '#718096';
}
