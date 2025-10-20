import React from "react";
import styles from "./RecommendationCard.module.css";

interface Recommendation {
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  action_items: string[];
}

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
}) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "#dc3545";
      case "medium":
        return "#ffc107";
      case "low":
        return "#28a745";
      default:
        return "#007acc";
    }
  };

  const priorityColor = getPriorityColor(recommendation.priority);

  return (
    <div className={styles.card} style={{ borderLeftColor: priorityColor }}>
      <div className={styles.header}>
        <div className={styles.title}>{recommendation.title}</div>
        <div className={styles.priority} style={{ color: priorityColor }}>
          {recommendation.priority.toUpperCase()}
        </div>
      </div>
      <div className={styles.description}>{recommendation.description}</div>
      {recommendation.action_items.length > 0 && (
        <div className={styles.actionItems}>
          <div className={styles.actionTitle}>Action Items:</div>
          <ul className={styles.actionList}>
            {recommendation.action_items.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
