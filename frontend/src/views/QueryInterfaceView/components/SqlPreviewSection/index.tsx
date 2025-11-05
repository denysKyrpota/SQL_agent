/**
 * SqlPreviewSection Component
 *
 * Container component displaying generated SQL with syntax highlighting,
 * copy functionality, and execution button.
 */

import React from 'react';
import type { SqlPreviewSectionProps } from '../../types';
import Button from '@/components/Button';
import SqlPreview from './SqlPreview';
import './SqlPreviewSection.module.css';

const SqlPreviewSection: React.FC<SqlPreviewSectionProps> = ({
  sql,
  onExecute,
  onCopy,
  executing,
}) => {
  return (
    <section className="sql-preview-section" aria-labelledby="sql-preview-heading">
      <h2 id="sql-preview-heading">Generated SQL</h2>
      <div className="sql-preview-container">
        <SqlPreview sql={sql} showLineNumbers={true} />
      </div>
      <div className="sql-actions">
        <Button
          variant="secondary"
          onClick={onCopy}
          ariaLabel="Copy SQL to clipboard"
        >
          Copy SQL
        </Button>
        <Button
          variant="primary"
          onClick={onExecute}
          disabled={executing}
          loading={executing}
          ariaLabel={executing ? 'Executing query' : 'Execute query'}
        >
          Execute Query
        </Button>
      </div>
    </section>
  );
};

export default SqlPreviewSection;
