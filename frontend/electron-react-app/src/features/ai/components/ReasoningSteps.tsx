import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Brain, CheckCircle, AlertCircle, Clock } from '../../../components/ui/Icons';
import styles from './ReasoningSteps.module.css';

interface ReasoningStep {
  id: string;
  step_number: number;
  description: string;
  reasoning: string;
  confidence: number;
  status: 'completed' | 'in_progress' | 'pending' | 'error';
  evidence?: string[];
  duration_ms?: number;
  sub_steps?: ReasoningStep[];
}

interface ReasoningStepsProps {
  steps: ReasoningStep[];
  title?: string;
  showConfidence?: boolean;
  expandable?: boolean;
  className?: string;
}

export const ReasoningSteps: React.FC<ReasoningStepsProps> = ({
  steps,
  title = "AI Reasoning Process",
  showConfidence = true,
  expandable = true,
  className = ''
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [isMainExpanded, setIsMainExpanded] = useState(true);

  const toggleStep = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} className={styles.statusCompleted} />;
      case 'in_progress':
        return <Clock size={16} className={styles.statusInProgress} />;
      case 'error':
        return <AlertCircle size={16} className={styles.statusError} />;
      default:
        return <div className={styles.statusPending} />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return styles.confidenceHigh;
    if (confidence >= 0.6) return styles.confidenceMedium;
    return styles.confidenceLow;
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const renderStep = (step: ReasoningStep, level: number = 0) => {
    const isExpanded = expandedSteps.has(step.id);
    const hasSubSteps = step.sub_steps && step.sub_steps.length > 0;
    const hasEvidence = step.evidence && step.evidence.length > 0;

    return (
      <div key={step.id} className={`${styles.step} ${styles[`level${level}`]}`}>
        <div className={styles.stepHeader}>
          <div className={styles.stepLeft}>
            {expandable && (hasSubSteps || hasEvidence || step.reasoning) && (
              <button
                onClick={() => toggleStep(step.id)}
                className={styles.expandButton}
                aria-label={isExpanded ? 'Collapse step' : 'Expand step'}
              >
                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
            )}
            <div className={styles.stepNumber}>{step.step_number}</div>
            {getStatusIcon(step.status)}
          </div>

          <div className={styles.stepContent}>
            <div className={styles.stepDescription}>{step.description}</div>
            <div className={styles.stepMeta}>
              {showConfidence && (
                <span className={`${styles.confidence} ${getConfidenceColor(step.confidence)}`}>
                  {Math.round(step.confidence * 100)}% confident
                </span>
              )}
              {step.duration_ms && (
                <span className={styles.duration}>
                  {formatDuration(step.duration_ms)}
                </span>
              )}
            </div>
          </div>
        </div>

        {isExpanded && (
          <div className={styles.stepDetails}>
            {step.reasoning && (
              <div className={styles.reasoning}>
                <h4>Reasoning:</h4>
                <p>{step.reasoning}</p>
              </div>
            )}

            {hasEvidence && (
              <div className={styles.evidence}>
                <h4>Evidence:</h4>
                <ul>
                  {step.evidence!.map((evidence, index) => (
                    <li key={index}>{evidence}</li>
                  ))}
                </ul>
              </div>
            )}

            {hasSubSteps && (
              <div className={styles.subSteps}>
                <h4>Sub-steps:</h4>
                {step.sub_steps!.map(subStep => renderStep(subStep, level + 1))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  if (!steps || steps.length === 0) {
    return (
      <div className={`${styles.container} ${className}`}>
        <div className={styles.emptyState}>
          <Brain size={48} className={styles.emptyIcon} />
          <p>No reasoning steps available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`}>
      <div className={styles.header}>
        {expandable && (
          <button
            onClick={() => setIsMainExpanded(!isMainExpanded)}
            className={styles.mainExpandButton}
            aria-label={isMainExpanded ? 'Collapse reasoning' : 'Expand reasoning'}
          >
            {isMainExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </button>
        )}
        <Brain size={20} className={styles.headerIcon} />
        <h3>{title}</h3>
        <div className={styles.headerMeta}>
          <span className={styles.stepCount}>{steps.length} steps</span>
        </div>
      </div>

      {isMainExpanded && (
        <div className={styles.stepsContainer}>
          {steps.map(step => renderStep(step))}
        </div>
      )}
    </div>
  );
};

// Hook for fetching reasoning steps from analysis results
export const useReasoningSteps = (analysisId?: string) => {
  const [steps, setSteps] = useState<ReasoningStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (!analysisId) return;

    const fetchReasoningSteps = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/analysis/${analysisId}/reasoning`);
        if (!response.ok) {
          throw new Error('Failed to fetch reasoning steps');
        }

        const data = await response.json();
        setSteps(data.reasoning_steps || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setSteps([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReasoningSteps();
  }, [analysisId]);

  return { steps, isLoading, error, refetch: () => {} };
};