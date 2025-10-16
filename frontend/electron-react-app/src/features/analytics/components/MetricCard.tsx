import React from 'react';
import { StatusChip } from '../../../components/ui/StatusChip';
import styles from './MetricCard.module.css';

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  color: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, color }) => {
  const isPositive = change.includes('↑');
  const changeColor = isPositive ? '#28a745' : '#dc3545';

  return (
    <div className={styles.card} style={{ borderLeftColor: color }}>
      <div className={styles.title}>{title}</div>
      <div className={styles.value} style={{ color }}>{value}</div>
      <div className={styles.change} style={{ color: changeColor }}>{change}</div>
    </div>
  );
};