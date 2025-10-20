import React from "react";
import styles from "./ConfidenceIndicator.module.css";

interface ConfidenceIndicatorProps {
  confidence: number;
  originalConfidence?: number;
  isCalibrated?: boolean;
  showDetails?: boolean;
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  confidence,
  originalConfidence,
  isCalibrated = false,
  showDetails = false,
}) => {
  const getConfidenceLevel = (score: number) => {
    if (score >= 0.8)
      return { level: "high", color: "#28a745", label: "High Confidence" };
    if (score >= 0.6)
      return { level: "medium", color: "#ffc107", label: "Medium Confidence" };
    return { level: "low", color: "#dc3545", label: "Low Confidence" };
  };

  const { level, color, label } = getConfidenceLevel(confidence);
  const percentage = Math.round(confidence * 100);

  return (
    <div className={styles.container}>
      <div className={styles.indicator}>
        <div
          className={`${styles.badge} ${styles[level]}`}
          style={{ backgroundColor: color }}
        >
          {percentage}%
        </div>
        {isCalibrated && (
          <div
            className={styles.calibratedIcon}
            title="Confidence score has been calibrated"
          >
            🎯
          </div>
        )}
      </div>

      {showDetails && (
        <div className={styles.details}>
          <div className={styles.label}>{label}</div>
          {isCalibrated && originalConfidence && (
            <div className={styles.calibrationInfo}>
              <span className={styles.originalScore}>
                Original: {Math.round(originalConfidence * 100)}%
              </span>
              <span className={styles.arrow}>→</span>
              <span className={styles.calibratedScore}>
                Calibrated: {percentage}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
