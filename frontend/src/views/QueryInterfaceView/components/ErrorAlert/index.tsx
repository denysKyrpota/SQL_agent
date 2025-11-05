/**
 * ErrorAlert Component
 *
 * Contextual error message display with icon, message text,
 * and optional action button for error recovery.
 */

import React from 'react';
import type { ErrorAlertProps } from '../../types';
import Button from '@/components/Button';
import { getRecoverySuggestion } from '../../utils/errorMessages';
import './ErrorAlert.module.css';

// Error icons based on type
const ERROR_ICONS: Record<string, string> = {
  validation: '⚠️',
  generation: '🔄',
  execution: '❌',
  timeout: '⏱️',
  network: '🌐',
};

const ErrorAlert: React.FC<ErrorAlertProps> = ({
  type,
  message,
  detail,
  dismissible = true,
  onDismiss,
  action,
}) => {
  const icon = ERROR_ICONS[type] || '⚠️';
  const suggestion = getRecoverySuggestion(type);

  return (
    <div
      role="alert"
      className={`error-alert error-alert-${type}`}
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="error-icon" aria-hidden="true">
        {icon}
      </div>
      <div className="error-content">
        <p className="error-message">{message}</p>
        {detail && <p className="error-detail">{detail}</p>}
        {suggestion && <p className="error-suggestion">{suggestion}</p>}
      </div>
      <div className="error-actions">
        {action && (
          <Button
            variant="secondary"
            onClick={action.onClick}
            ariaLabel={action.label}
          >
            {action.label}
          </Button>
        )}
        {dismissible && onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="error-dismiss-btn"
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorAlert;
