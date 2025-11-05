/**
 * LoadingIndicator Component
 *
 * Two-stage loading indicator showing current processing stage
 * with animated spinner and descriptive text.
 */

import React from 'react';
import type { LoadingIndicatorProps } from '../../types';
import './LoadingIndicator.module.css';

const STAGE_MESSAGES = {
  schema: 'Analyzing database schema...',
  generation: 'Generating SQL query...',
  execution: 'Running query...',
};

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ stage, startTime }) => {
  const message = STAGE_MESSAGES[stage];

  return (
    <div className="loading-indicator">
      <div className="spinner" aria-hidden="true"></div>
      <p className="loading-text">{message}</p>
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {message}
      </div>
    </div>
  );
};

export default LoadingIndicator;
