import React from "react";
import styles from "./HabitProgressBar.module.css";

interface HabitProgressBarProps {
  habitName: string;
  percentage: number;
  masteryLevel: "Mastered" | "Proficient" | "Developing" | "Needs Focus";
}

export const HabitProgressBar: React.FC<HabitProgressBarProps> = ({
  habitName,
  percentage,
  masteryLevel,
}) => {
  const getMasteryColor = (level: string) => {
    switch (level) {
      case "Mastered":
        return "#27ae60";
      case "Proficient":
        return "#2980b9";
      case "Developing":
        return "#f39c12";
      case "Needs Focus":
        return "#e74c3c";
      default:
        return "#6c757d";
    }
  };

  const masteryColor = getMasteryColor(masteryLevel);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.habitName}>{habitName}</div>
        <div className={styles.masteryLevel} style={{ color: masteryColor }}>
          {masteryLevel}
        </div>
      </div>
      <div className={styles.progressContainer}>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{
              width: `${Math.min(percentage, 100)}%`,
              backgroundColor: masteryColor,
            }}
          />
        </div>
        <div className={styles.percentage}>{percentage}%</div>
      </div>
    </div>
  );
};
