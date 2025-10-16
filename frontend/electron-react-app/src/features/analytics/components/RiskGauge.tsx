import React from 'react';
import styles from './RiskGauge.module.css';

interface RiskGaugeProps {
  riskScore: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ riskScore }) => {
  const getRiskLevel = (score: number) => {
    if (score < 10) {
      return { level: 'LOW RISK', color: '#28a745' };
    } else if (score < 25) {
      return { level: 'MODERATE RISK', color: '#ffc107' };
    } else {
      return { level: 'HIGH RISK', color: '#dc3545' };
    }
  };

  const { level, color } = getRiskLevel(riskScore);

  return (
    <div className={styles.container}>
      <div className={styles.title}>Current Audit Risk Level</div>
      <div className={styles.value} style={{ color }}>
        {riskScore}%
      </div>
      <div className={styles.level} style={{ color }}>
        {level}
      </div>
    </div>
  );
};