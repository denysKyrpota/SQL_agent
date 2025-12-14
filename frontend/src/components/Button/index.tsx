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
  size = 'medium',
  disabled = false,
  loading = false,
  type = 'button',
  icon,
  fullWidth = false,
  ariaLabel,
  className,
}) => {
  const handleClick = () => {
    if (!disabled && !loading && onClick) {
      onClick();
    }
  };

  const classNames = [
    'button',
    `button-${variant}`,
    `button-${size}`,
    fullWidth ? 'button-full-width' : '',
    loading ? 'button-loading' : '',
    className || '',
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
      {!loading && icon && (
        <span className="button-icon" aria-hidden="true">{icon}</span>
      )}
      {!loading && <span className="button-content">{children}</span>}
      {loading && <span className="button-content" style={{ visibility: 'hidden' }}>{children}</span>}
    </button>
  );
};

export default Button;
