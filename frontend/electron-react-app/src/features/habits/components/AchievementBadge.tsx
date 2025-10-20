import React from "react";
import styles from "./AchievementBadge.module.css";

interface Achievement {
  id: string;
  title: string;
  description: string;
  earned_date: string;
  badge_type: string;
}

interface AchievementBadgeProps {
  achievement: Achievement;
}

export const AchievementBadge: React.FC<AchievementBadgeProps> = ({
  achievement,
}) => {
  const getBadgeIcon = (badgeType: string) => {
    switch (badgeType) {
      case "streak":
        return "🔥";
      case "improvement":
        return "📈";
      case "mastery":
        return "🏆";
      case "consistency":
        return "⭐";
      default:
        return "🎯";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className={styles.badge}>
      <div className={styles.icon}>{getBadgeIcon(achievement.badge_type)}</div>
      <div className={styles.content}>
        <div className={styles.title}>{achievement.title}</div>
        <div className={styles.description}>{achievement.description}</div>
        <div className={styles.date}>
          Earned {formatDate(achievement.earned_date)}
        </div>
      </div>
    </div>
  );
};
