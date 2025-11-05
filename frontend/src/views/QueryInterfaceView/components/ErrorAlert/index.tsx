/**
 * ErrorAlert Component
 *
 * Contextual error message display with icon, message text,
 * and optional action button for error recovery.
 */

import React from 'react';
import type { ErrorAlertProps } from '../../types';
import './ErrorAlert.module.css';

const ErrorAlert: React.FC<ErrorAlertProps> = ({
  type,
  message,
  detail,
  dismissible = true,
  onDismiss,
  action,
}) => {
  return (
    <div role="alert" className={`error-alert error-alert-${type}`}>
      <div className="error-icon" aria-hidden="true">⚠</div>
      <div className="error-content">
        <p className="error-message">{message}</p>
        {detail && <p className="error-detail">{detail}</p>}
      </div>
      <div className="error-actions">
        {action && (
          <button
            type="button"
            onClick={action.onClick}
            className="error-action-btn"
          >
            {action.label}
          </button>
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
