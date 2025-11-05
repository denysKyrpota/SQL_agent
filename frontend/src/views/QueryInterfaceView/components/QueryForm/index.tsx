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
import ExampleQuestions from './ExampleQuestions';
import { validateQuery } from '../../utils/validation';
import './QueryForm.module.css';

const MAX_QUERY_LENGTH = 5000;

const QueryForm: React.FC<QueryFormProps> = ({
  value,
  onChange,
  onSubmit,
  disabled,
  examples,
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

  const handleExampleSelect = (example: string) => {
    onChange(example);
    setValidationError(null);
  };

  const isSubmitDisabled = disabled || value.trim().length === 0;

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <div className="form-header">
          <label htmlFor="query-input" className="form-label">
            Enter your database question
          </label>
          <CharacterCount
            current={value.length}
            max={MAX_QUERY_LENGTH}
          />
        </div>

        <TextArea
          id="query-input"
          value={value}
          onChange={handleChange}
          maxLength={MAX_QUERY_LENGTH}
          placeholder="e.g., What were our top 10 customers by revenue last quarter?"
          disabled={disabled}
          autoFocus={true}
          label=""
        />

        {validationError && (
          <div className="form-error" role="alert">
            {validationError}
          </div>
        )}
      </div>

      <ExampleQuestions
        examples={examples}
        onSelect={handleExampleSelect}
        disabled={disabled}
      />

      <div className="form-actions">
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
