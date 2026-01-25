/**
 * Query Filters - Filter queries by status
 */

import React from 'react';
import type { QueryStatus } from '@/types/common';
import styles from './QueryFilters.module.css';

interface QueryFiltersProps {
  currentFilter: QueryStatus | 'all';
  onFilterChange: (status: QueryStatus | 'all') => void;
}

const QueryFilters: React.FC<QueryFiltersProps> = ({
  currentFilter,
  onFilterChange,
}) => {
  const filters: Array<{ value: QueryStatus | 'all'; label: string; count?: number }> = [
    { value: 'all', label: 'All Queries' },
    { value: 'not_executed', label: 'Not Executed' },
    { value: 'success', label: 'Success' },
    { value: 'failed_generation', label: 'Failed Generation' },
    { value: 'failed_execution', label: 'Failed Execution' },
    { value: 'timeout', label: 'Timeout' },
  ];

  return (
    <div className={styles['query-filters']}>
      <div className={styles['filter-label']}>Filter by status:</div>
      <div className={styles['filter-buttons']}>
        {filters.map((filter) => (
          <button
            key={filter.value}
            className={`${styles['filter-button']} ${
              currentFilter === filter.value ? styles['active'] : ''
            }`}
            onClick={() => onFilterChange(filter.value)}
          >
            {filter.label}
            {filter.count !== undefined && (
              <span className={styles['filter-count']}>{filter.count}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default QueryFilters;
