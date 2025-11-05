/**
 * SqlPreviewSection Component
 *
 * Container component displaying generated SQL with syntax highlighting,
 * copy functionality, and execution button.
 */

import React from 'react';
import type { SqlPreviewSectionProps } from '../../types';
import './SqlPreviewSection.module.css';

const SqlPreviewSection: React.FC<SqlPreviewSectionProps> = ({
  sql,
  onExecute,
  onCopy,
  executing,
}) => {
  return (
    <section className="sql-preview-section">
      <h2>Generated SQL</h2>
      <div className="sql-preview-container">
        {/* TODO: Implement SqlPreview component with syntax highlighting */}
        <pre className="sql-preview">
          <code>{sql}</code>
        </pre>
      </div>
      <div className="sql-actions">
        <button
          type="button"
          onClick={onCopy}
          className="btn-secondary"
        >
          Copy SQL
        </button>
        <button
          type="button"
          onClick={onExecute}
          disabled={executing}
          className="btn-primary"
        >
          {executing ? 'Executing...' : 'Execute Query'}
        </button>
      </div>
    </section>
  );
};

export default SqlPreviewSection;
