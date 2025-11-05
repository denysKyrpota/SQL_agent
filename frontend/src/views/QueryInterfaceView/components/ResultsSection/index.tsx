/**
 * ResultsSection Component
 *
 * Container component displaying query execution results including
 * performance metrics, data table, pagination, and export functionality.
 */

import React from 'react';
import type { ResultsSectionProps } from '../../types';
import Button from '@/components/Button';
import Pagination from '@/components/Pagination';
import PerformanceMetrics from './PerformanceMetrics';
import ResultsTable from './ResultsTable';
import './ResultsSection.module.css';

const ResultsSection: React.FC<ResultsSectionProps> = ({
  results,
  currentPage,
  onPageChange,
  onExport,
  generationTimeMs,
  executionTimeMs,
}) => {
  // Check if export should show warning
  const shouldWarnExport = results.total_rows > 10000;

  const handleExport = () => {
    if (shouldWarnExport) {
      if (confirm(`Results contain ${results.total_rows.toLocaleString()} rows. Export will be limited to first 10,000 rows. Continue?`)) {
        onExport();
      }
    } else {
      onExport();
    }
  };

  return (
    <section className="results-section" aria-labelledby="results-heading">
      <div className="results-header">
        <h2 id="results-heading">Query Results</h2>
        <Button
          variant="secondary"
          onClick={handleExport}
          ariaLabel={shouldWarnExport ? 'Export CSV (limited to 10,000 rows)' : 'Export CSV'}
        >
          Export CSV
        </Button>
      </div>

      <PerformanceMetrics
        generationTimeMs={generationTimeMs}
        executionTimeMs={executionTimeMs}
        rowCount={results.total_rows}
      />

      <ResultsTable
        columns={results.columns}
        rows={results.rows}
        totalRows={results.total_rows}
      />

      {results.page_count > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={results.page_count}
          pageSize={results.page_size}
          totalRows={results.total_rows}
          onPageChange={onPageChange}
        />
      )}
    </section>
  );
};

export default ResultsSection;
