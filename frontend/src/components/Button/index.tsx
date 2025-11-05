/**
 * Button Component
 *
 * Reusable action button with variants, loading states, and icon support.
 */

import React from 'react';
import type { ButtonProps } from '@/views/QueryInterfaceView/types';
import './Button.module.css';

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  loading = false,
  type = 'button',
  icon,
  fullWidth = false,
  ariaLabel,
}) => {
  const handleClick = () => {
    if (!disabled && !loading) {
      onClick();
    }
  };

  const classNames = [
    'btn',
    `btn-${variant}`,
    fullWidth ? 'btn-full-width' : '',
    loading ? 'btn-loading' : '',
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      className={classNames}
      onClick={handleClick}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-busy={loading}
    >
      {loading && (
        <span className="btn-spinner" aria-hidden="true"></span>
      )}
      {!loading && icon && (
        <span className="btn-icon" aria-hidden="true">{icon}</span>
      )}
      <span className="btn-content">{children}</span>
    </button>
  );
};

export default Button;
