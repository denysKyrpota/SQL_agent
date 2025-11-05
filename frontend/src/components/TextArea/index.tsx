/**
 * TextArea Component
 *
 * Multi-line text input component with auto-resize, character limit enforcement,
 * and accessibility features.
 */

import React, { useEffect, useRef } from 'react';
import type { TextAreaProps } from '@/views/QueryInterfaceView/types';
import './TextArea.module.css';

const TextArea: React.FC<TextAreaProps> = ({
  value,
  onChange,
  maxLength,
  placeholder,
  disabled,
  autoFocus = false,
  label,
  id,
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
    'textarea',
    isNearLimit ? 'textarea-warning' : '',
    isAtLimit ? 'textarea-error' : '',
    disabled ? 'textarea-disabled' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className="textarea-wrapper">
      <label htmlFor={id} className="textarea-label">
        {label}
      </label>
      <textarea
        ref={textareaRef}
        id={id}
        className={textareaClasses}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        maxLength={maxLength}
        rows={4}
        aria-describedby={`${id}-char-count`}
      />
    </div>
  );
};

export default TextArea;
