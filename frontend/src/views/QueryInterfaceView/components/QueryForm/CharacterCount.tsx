/**
 * CharacterCount Component
 *
 * Display component showing current character count with visual feedback
 * as limit approaches.
 */

import React from 'react';
import type { CharacterCountProps } from '../../types';
import './CharacterCount.css';

const CharacterCount: React.FC<CharacterCountProps> = ({ current, max }) => {
  // Determine color state based on percentage
  const percentage = (current / max) * 100;

  let stateClass = '';
  if (percentage >= 98) {
    stateClass = 'critical';
  } else if (percentage >= 90) {
    stateClass = 'danger';
  } else if (percentage >= 80) {
    stateClass = 'warning';
  }

  const classNames = ['character-count', stateClass].filter(Boolean).join(' ');

  // Announce to screen readers at key thresholds
  const shouldAnnounce = percentage >= 80;

  return (
    <div className={classNames} id="character-count">
      <span className="current">{current}</span>
      <span className="separator">/</span>
      <span className="max">{max}</span>
      {shouldAnnounce && (
        <span className="sr-only" role="status" aria-live="polite">
          {current} of {max} characters used
        </span>
      )}
    </div>
  );
};

export default CharacterCount;
