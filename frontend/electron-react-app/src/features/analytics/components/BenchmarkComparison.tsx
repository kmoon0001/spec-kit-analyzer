import React from 'react';
import styles from './BenchmarkComparison.module.css';

interface BenchmarkComparisonProps {
  name: string;
  yourScore: number;
  industryAvg: number;
  topPerformer: number;
}

export const BenchmarkComparison: React.FC<BenchmarkComparisonProps> = ({
  name,
  yourScore,
  industryAvg,
  topPerformer,
}) => {
  const comparisons = [
    { label: 'Your Performance', score: yourScore, color: '#007acc' },
    { label: 'Industry Average', score: industryAvg, color: '#6c757d' },
    { label: 'Top Performers', score: topPerformer, color: '#28a745' },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.title}>{name}</div>
      <div className={styles.comparisons}>
        {comparisons.map((comparison) => (
          <div key={comparison.label} className={styles.comparisonRow}>
            <div className={styles.label}>{comparison.label}</div>
            <div className={styles.progressContainer}>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{
                    width: `${comparison.score}%`,
                    backgroundColor: comparison.color,
                  }}
                />
              </div>
              <div className={styles.score} style={{ color: comparison.color }}>
                {comparison.score}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};