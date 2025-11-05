/**
 * ResultsSection Component
 *
 * Container component displaying query execution results including
 * performance metrics, data table, pagination, and export functionality.
 */

import React from 'react';
import type { ResultsSectionProps } from '../../types';
import './ResultsSection.module.css';

const ResultsSection: React.FC<ResultsSectionProps> = ({
  results,
  currentPage,
  onPageChange,
  onExport,
  generationTimeMs,
  executionTimeMs,
}) => {
  return (
    <section className="results-section">
      <h2>Query Results</h2>

      {/* TODO: Implement PerformanceMetrics component */}
      <div className="results-metrics">
        <span>Generation: {generationTimeMs}ms</span>
        <span>Execution: {executionTimeMs}ms</span>
        <span>Rows: {results.total_rows}</span>
      </div>

      {/* TODO: Implement ResultsTable component */}
      <div className="results-table-wrapper">
        <table className="results-table">
          <thead>
            <tr>
              {results.columns.map((col, idx) => (
                <th key={idx} scope="col">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.rows.map((row, rowIdx) => (
              <tr key={rowIdx}>
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx}>{cell !== null ? String(cell) : 'NULL'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* TODO: Implement Pagination component */}
      {results.page_count > 1 && (
        <div className="results-pagination">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span>Page {currentPage} of {results.page_count}</span>
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === results.page_count}
          >
            Next
          </button>
        </div>
      )}

      <div className="results-actions">
        <button onClick={onExport} className="btn-export">
          Export CSV
        </button>
      </div>
    </section>
  );
};

export default ResultsSection;
