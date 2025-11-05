/**
 * SqlPreview Component
 *
 * Display component showing SQL code with syntax highlighting and line numbers.
 * Uses a simple custom highlighter since react-syntax-highlighter may not be installed.
 */

import React from 'react';
import type { SqlPreviewProps } from '../../types';
import './SqlPreview.css';

/**
 * Simple SQL keyword highlighter
 */
const highlightSQL = (sql: string): string => {
  const keywords = [
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
    'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL',
    'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'AS',
    'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TABLE',
    'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CASE', 'WHEN',
    'THEN', 'ELSE', 'END', 'WITH', 'UNION', 'INTERSECT', 'EXCEPT',
  ];

  let highlighted = sql;

  // Highlight SQL keywords
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
    highlighted = highlighted.replace(
      regex,
      `<span class="sql-keyword">${keyword.toUpperCase()}</span>`
    );
  });

  // Highlight strings (single and double quotes)
  highlighted = highlighted.replace(
    /'([^']*)'/g,
    '<span class="sql-string">\'$1\'</span>'
  );
  highlighted = highlighted.replace(
    /"([^"]*)"/g,
    '<span class="sql-string">"$1"</span>'
  );

  // Highlight numbers
  highlighted = highlighted.replace(
    /\b(\d+)\b/g,
    '<span class="sql-number">$1</span>'
  );

  // Highlight comments
  highlighted = highlighted.replace(
    /--([^\n]*)/g,
    '<span class="sql-comment">--$1</span>'
  );

  return highlighted;
};

const SqlPreview: React.FC<SqlPreviewProps> = ({
  sql,
  showLineNumbers = true,
  language = 'sql',
}) => {
  const lines = sql.split('\n');
  const highlightedSQL = highlightSQL(sql);

  return (
    <div className="sql-preview-wrapper">
      {showLineNumbers && (
        <div className="sql-line-numbers" aria-hidden="true">
          {lines.map((_, index) => (
            <div key={index} className="line-number">
              {index + 1}
            </div>
          ))}
        </div>
      )}
      <pre className="sql-preview">
        <code
          className={`language-${language}`}
          dangerouslySetInnerHTML={{ __html: highlightedSQL }}
        />
      </pre>
    </div>
  );
};

export default SqlPreview;
