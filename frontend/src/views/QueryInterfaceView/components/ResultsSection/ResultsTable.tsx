/**
 * ResultsTable Component
 *
 * Data grid component displaying query results with proper table semantics,
 * responsive columns, and alternating row colors.
 */

import React from 'react';
import type { ResultsTableProps } from '../../types';
import './ResultsTable.css';

/**
 * Detect column type based on data
 */
const detectColumnType = (value: any): 'id' | 'number' | 'date' | 'boolean' | 'text' => {
  if (value === null || value === undefined) return 'text';

  const str = String(value);

  // Check if it looks like an ID (ends with _id or is named id)
  // This would need column name context, so we'll do simple detection

  // Check for boolean
  if (value === true || value === false || str === 'true' || str === 'false') {
    return 'boolean';
  }

  // Check for number
  if (!isNaN(Number(value)) && str.trim() !== '') {
    return 'number';
  }

  // Check for date (ISO 8601 format)
  if (/^\d{4}-\d{2}-\d{2}/.test(str)) {
    return 'date';
  }

  return 'text';
};

/**
 * Get column width class based on type
 */
const getColumnClass = (columnName: string, sampleValue: any): string => {
  const type = detectColumnType(sampleValue);
  const name = columnName.toLowerCase();

  if (name.endsWith('_id') || name === 'id') {
    return 'col-id';
  }

  switch (type) {
    case 'id':
    case 'number':
    case 'boolean':
      return 'col-narrow';
    case 'date':
      return 'col-medium';
    default:
      return 'col-wide';
  }
};

/**
 * Format cell value for display
 */
const formatCellValue = (value: any): string => {
  if (value === null || value === undefined) {
    return 'NULL';
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }

  return String(value);
};

const ResultsTable: React.FC<ResultsTableProps> = ({
  columns,
  rows,
  totalRows: _totalRows,
}) => {
  if (rows.length === 0) {
    return (
      <div className="results-empty">
        <p>No rows returned</p>
      </div>
    );
  }

  // Get sample values for column width detection
  const sampleRow = rows[0] || [];

  return (
    <div className="results-table-wrapper">
      <table className="results-table">
        <thead>
          <tr>
            {columns.map((column, idx) => (
              <th
                key={idx}
                scope="col"
                className={getColumnClass(column, sampleRow[idx])}
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr key={rowIdx}>
              {row.map((cell, cellIdx) => (
                <td
                  key={cellIdx}
                  className={getColumnClass(columns[cellIdx], cell)}
                  title={formatCellValue(cell)}
                >
                  {formatCellValue(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;
