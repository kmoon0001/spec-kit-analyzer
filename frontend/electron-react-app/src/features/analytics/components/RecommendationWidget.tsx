import React from 'react';
import styles from './RecommendationWidget.module.css';

interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  action: string;
  impact: string;
  effort: string;
}

interface RecommendationWidgetProps {
  recommendation: Recommendation;
}

export const RecommendationWidget: React.FC<RecommendationWidgetProps> = ({ recommendation }) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#dc3545';
      case 'medium':
        return '#ffc107';
      case 'low':
        return '#28a745';
      default:
        return '#007acc';
    }
  };

  const priorityColor = getPriorityColor(recommendation.priority);

  return (
    <div className={styles.widget} style={{ borderLeftColor: priorityColor }}>
      <div className={styles.priority} style={{ color: priorityColor }}>
        {recommendation.priority.toUpperCase()} PRIORITY
      </div>
      <div className={styles.action}>{recommendation.action}</div>
      <div className={styles.details}>
        <div className={styles.impact}>Expected Impact: {recommendation.impact}</div>
        <div className={styles.effort}>Effort Required: {recommendation.effort}</div>
      </div>
    </div>
  );
};