/**
 * ExampleQuestions Component
 *
 * Display component showing clickable example questions to help users
 * understand query patterns. Clicking an example loads pre-existing SQL
 * directly into the chat without LLM generation.
 */

import React from 'react';
import type { ExampleQuestionsProps, ExampleQuestion } from '../../types';
import './ExampleQuestions.css';

const ExampleQuestions: React.FC<ExampleQuestionsProps> = ({
  examples,
  onSelect,
  disabled,
}) => {
  const handleClick = (example: ExampleQuestion) => {
    if (!disabled) {
      onSelect(example);
    }
  };

  if (examples.length === 0) {
    return null;
  }

  return (
    <div className="example-questions">
      <h3 className="example-questions-title">Example Questions</h3>
      <ul className="examples-list">
        {examples.map((example, index) => (
          <li key={example.filename || index} className="example-item">
            <button
              type="button"
              className="example-button"
              onClick={() => handleClick(example)}
              disabled={disabled}
              aria-label={`Use example: ${example.title}`}
            >
              <span className="example-icon" aria-hidden="true">💡</span>
              <span className="example-text">{example.title}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ExampleQuestions;
