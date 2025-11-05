/**
 * Pagination Component
 *
 * Page navigation component for large result sets with Previous/Next buttons
 * and page information display.
 */

import React from 'react';
import type { PaginationProps } from '@/views/QueryInterfaceView/types';
import Button from '../Button';
import './Pagination.module.css';

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  pageSize,
  totalRows,
  onPageChange,
}) => {
  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  const startRow = (currentPage - 1) * pageSize + 1;
  const endRow = Math.min(currentPage * pageSize, totalRows);

  return (
    <nav
      className="pagination"
      aria-label="Results pagination"
      role="navigation"
    >
      <Button
        variant="secondary"
        onClick={handlePrevious}
        disabled={currentPage === 1}
        ariaLabel="Go to previous page"
      >
        Previous
      </Button>

      <div className="pagination-info">
        <span className="page-indicator">
          Page {currentPage} of {totalPages}
        </span>
        <span className="row-indicator">
          Showing {startRow.toLocaleString()}-{endRow.toLocaleString()} of {totalRows.toLocaleString()} rows
        </span>
      </div>

      <Button
        variant="secondary"
        onClick={handleNext}
        disabled={currentPage === totalPages}
        ariaLabel="Go to next page"
      >
        Next
      </Button>

      {/* Screen reader announcement */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        Page {currentPage} of {totalPages}
      </div>
    </nav>
  );
};

export default Pagination;
