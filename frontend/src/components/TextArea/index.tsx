/**
 * TextArea Component
 *
 * Multi-line text input component with auto-resize, character limit enforcement,
 * and accessibility features.
 */

import React, { useEffect, useRef } from 'react';
import type { TextAreaProps } from '@/views/QueryInterfaceView/types';
import styles from './TextArea.module.css';

const TextArea: React.FC<TextAreaProps> = ({
  value,
  onChange,
  maxLength = 5000,
  placeholder,
  disabled = false,
  autoFocus = false,
  label,
  id,
  rows = 4,
  onKeyDown,
  className,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    if (newValue.length <= maxLength) {
      onChange(newValue);
    }
  };

  // Determine warning state based on character count
  const currentLength = value.length;
  const warningThreshold = maxLength * 0.9; // 90%
  const isNearLimit = currentLength >= warningThreshold;
  const isAtLimit = currentLength >= maxLength;

  const textareaClasses = [
    styles.textarea,
    isNearLimit ? styles['textarea-warning'] : '',
    isAtLimit ? styles['textarea-error'] : '',
    disabled ? styles['textarea-disabled'] : '',
    className || '',
  ].filter(Boolean).join(' ');

  return (
    <div className={styles['textarea-wrapper']}>
      {label && (
        <label htmlFor={id} className={styles['textarea-label']}>
          {label}
        </label>
      )}
      <textarea
        ref={textareaRef}
        id={id}
        className={textareaClasses}
        value={value}
        onChange={handleChange}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        maxLength={maxLength}
        rows={rows}
        aria-describedby={id ? `${id}-char-count` : undefined}
      />
    </div>
  );
};

export default TextArea;
