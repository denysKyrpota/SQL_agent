/**
 * LoadingIndicator Component
 *
 * Multi-stage loading indicator that shows progress through
 * the SQL generation pipeline with animated stages.
 */

import React, { useState, useEffect } from 'react';
import type { LoadingIndicatorProps } from '../../types';
import styles from './LoadingIndicator.module.css';

// Stage messages for schema/generation process (simulated progression)
const GENERATION_STAGES = [
  { message: 'Analyzing your question...', duration: 2000 },
  { message: 'Selecting relevant tables...', duration: 4000 },
  { message: 'Finding similar examples...', duration: 3000 },
  { message: 'Generating SQL query...', duration: 0 }, // Stays here until done
];

const EXECUTION_STAGES = [
  { message: 'Connecting to database...', duration: 1000 },
  { message: 'Running query...', duration: 0 },
];

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ stage }) => {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);

  const stages = stage === 'execution' ? EXECUTION_STAGES : GENERATION_STAGES;

  // Reset stage index when stage prop changes
  useEffect(() => {
    setCurrentStageIndex(0);
  }, [stage]);

  // Progress through stages based on timing
  useEffect(() => {
    const currentStage = stages[currentStageIndex];

    // If this stage has a duration, move to next stage after that time
    if (currentStage && currentStage.duration > 0 && currentStageIndex < stages.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStageIndex(prev => prev + 1);
      }, currentStage.duration);

      return () => clearTimeout(timer);
    }
  }, [currentStageIndex, stages]);

  const currentMessage = stages[currentStageIndex]?.message || 'Processing...';

  return (
    <div className={styles.loadingIndicator}>
      <div className={styles.spinner} aria-hidden="true"></div>
      <p className={styles.loadingText}>{currentMessage}</p>
      {/* Progress dots */}
      <div className={styles.progressDots}>
        {stages.map((_, index) => (
          <span
            key={index}
            className={`${styles.dot} ${index <= currentStageIndex ? styles.dotActive : ''}`}
          />
        ))}
      </div>
      <div aria-live="polite" aria-atomic="true" className={styles.srOnly}>
        {currentMessage}
      </div>
    </div>
  );
};

export default LoadingIndicator;
