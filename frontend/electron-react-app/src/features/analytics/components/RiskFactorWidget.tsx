import React from 'react';
import styles from './RiskFactorWidget.module.css';

interface RiskFactor {
  name: string;
  impact: number;
  trend: string;
}

interface RiskFactorWidgetProps {
  factor: RiskFactor;
}

export const RiskFactorWidget: React.FC<RiskFactorWidgetProps> = ({ factor }) => {
  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving':
        return '#28a745';
      case 'stable':
        return '#ffc107';
      case 'worsening':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  return (
    <div className={styles.widget}>
      <div className={styles.content}>
        <div className={styles.name}>{factor.name}</div>
        <div className={styles.metrics}>
          <div className={styles.impact}>
            Impact: <span className={styles.impactValue}>{factor.impact}%</span>
          </div>
          <div className={styles.trend} style={{ color: getTrendColor(factor.trend) }}>
            Trend: {factor.trend}
          </div>
        </div>
      </div>
    </div>
  );
};