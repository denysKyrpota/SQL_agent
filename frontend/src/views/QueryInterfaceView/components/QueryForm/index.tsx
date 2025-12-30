/**
 * QueryForm Component
 *
 * Form component for natural language query input with textarea,
 * character count, example questions, and submission button.
 */

import React, { useState } from 'react';
import type { QueryFormProps } from '../../types';
import TextArea from '@/components/TextArea';
import Button from '@/components/Button';
import CharacterCount from './CharacterCount';
import { validateQuery } from '../../utils/validation';
import styles from './QueryForm.module.css';

const MAX_QUERY_LENGTH = 5000;

const QueryForm: React.FC<QueryFormProps> = ({
  value,
  onChange,
  onSubmit,
  disabled,
}) => {
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate query before submission
    const error = validateQuery(value);
    if (error) {
      setValidationError(error);
      return;
    }

    setValidationError(null);
    onSubmit();
  };

  const handleChange = (newValue: string) => {
    onChange(newValue);
    // Clear validation error when user starts typing
    if (validationError) {
      setValidationError(null);
    }
  };

  const isSubmitDisabled = disabled || value.trim().length === 0;

  return (
    <form className={styles['query-form']} onSubmit={handleSubmit}>
      <div className={styles['form-group']}>
        {/* Only show header when user has typed something */}
        {value.length > 0 && (
          <div className={styles['form-header']}>
            <label htmlFor="query-input" className={styles['form-label']}>
              Your question
            </label>
            <CharacterCount
              current={value.length}
              max={MAX_QUERY_LENGTH}
            />
          </div>
        )}

        <TextArea
          id="query-input"
          value={value}
          onChange={handleChange}
          maxLength={MAX_QUERY_LENGTH}
          placeholder="Ask your database a question..."
          disabled={disabled}
          autoFocus={true}
          label=""
        />

        {validationError && (
          <div className={styles['form-error']} role="alert">
            {validationError}
          </div>
        )}
      </div>

      <div className={styles['form-actions']}>
        <Button
          type="submit"
          variant="primary"
          disabled={isSubmitDisabled}
          loading={disabled}
        >
          Generate SQL
        </Button>
      </div>
    </form>
  );
};

export default QueryForm;
