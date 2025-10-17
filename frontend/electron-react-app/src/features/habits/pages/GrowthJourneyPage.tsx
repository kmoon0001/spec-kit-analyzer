import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { useHabitsProgression } from '../hooks/useHabitsProgression';
import { HabitProgressBar } from '../components/HabitProgressBar';
import { AchievementBadge } from '../components/AchievementBadge';
import { RecommendationCard } from '../components/RecommendationCard';
import styles from './GrowthJourneyPage.module.css';

export default function GrowthJourneyPage() {
  const { progression, isLoading, isError, refetch } = useHabitsProgression();

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div>Loading your growth journey...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className={styles.error}>
        <div>Failed to load growth journey data</div>
        <Button onClick={refetch}>Retry</Button>
      </div>
    );
  }

  const getImprovementIcon = (rate: number) => {
    if (rate > 0) return '📈';
    if (rate < 0) return '📉';
    return '📊';
  };

  const getImprovementColor = (rate: number) => {
    if (rate > 0) return '#28a745';
    if (rate < 0) return '#dc3545';
    return '#6c757d';
  };

  const getImprovementText = (rate: number) => {
    if (rate > 0) return `+${rate}% improving`;
    if (rate < 0) return `${rate}% declining`;
    return 'Stable performance';
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h2>🌟 Personal Growth Journey</h2>
        <p>Track your habit mastery, progress trends, and achievements in the 7 Habits framework</p>
        <Button onClick={refetch} variant="outline" className={styles.refreshButton}>
          🔄 Refresh
        </Button>
      </header>

      {/* Overall Progress Summary */}
      <div className={styles.summaryCard}>
        <div className={styles.progressSection}>
          <div className={styles.progressValue}>
            {progression?.overall_progress?.percentage?.toFixed(1) || '0.0'}%
          </div>
          <div className={styles.progressStatus}>
            Status: {progression?.overall_progress?.status || 'Unknown'}
          </div>
        </div>
        <div className={styles.streakSection}>
          <div className={styles.streakValue}>
            🔥 {progression?.current_streak || 0} day streak
          </div>
        </div>
        <div className={styles.improvementSection}>
          <div
            className={styles.improvementValue}
            style={{ color: getImprovementColor(progression?.improvement_rate || 0) }}
          >
            {getImprovementIcon(progression?.improvement_rate || 0)} {getImprovementText(progression?.improvement_rate || 0)}
          </div>
        </div>
      </div>

      <div className={styles.content}>
        {/* Left Panel - Habit Mastery */}
        <div className={styles.leftPanel}>
          <Card title="📊 Habit Mastery Levels" className={styles.masteryCard}>
            <div className={styles.habitsList}>
              {progression?.habit_breakdown && Object.entries(progression.habit_breakdown)
                .sort(([a], [b]) => parseInt(a.split('_')[1]) - parseInt(b.split('_')[1]))
                .map(([habitId, habitData]) => (
                  <HabitProgressBar
                    key={habitId}
                    habitName={`Habit ${habitData.habit_number}: ${habitData.habit_name}`}
                    percentage={habitData.percentage}
                    masteryLevel={habitData.mastery_level}
                  />
                ))}
            </div>
          </Card>

          {/* Recent Achievements */}
          {progression?.achievements && progression.achievements.length > 0 && (
            <Card title="🏆 Recent Achievements" className={styles.achievementsCard}>
              <div className={styles.achievementsList}>
                {progression.achievements.slice(0, 3).map((achievement) => (
                  <AchievementBadge key={achievement.id} achievement={achievement} />
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Panel - Recommendations & Goals */}
        <div className={styles.rightPanel}>
          {/* Personalized Recommendations */}
          {progression?.recommendations && progression.recommendations.length > 0 && (
            <Card title="💡 Personalized Recommendations" className={styles.recommendationsCard}>
              <div className={styles.recommendationsList}>
                {progression.recommendations.slice(0, 3).map((recommendation, index) => (
                  <RecommendationCard key={index} recommendation={recommendation} />
                ))}
              </div>
            </Card>
          )}

          {/* Current Goals */}
          {progression?.current_goals && progression.current_goals.length > 0 && (
            <Card title="🎯 Current Goals" className={styles.goalsCard}>
              <div className={styles.goalsList}>
                {progression.current_goals.map((goal, index) => (
                  <div key={index} className={styles.goalItem}>
                    <div className={styles.goalHeader}>
                      <div className={styles.goalTitle}>{goal.title}</div>
                      <div className={styles.goalProgress}>{goal.progress}%</div>
                    </div>
                    <div className={styles.goalDescription}>{goal.description}</div>
                    <div className={styles.goalProgressBar}>
                      <div
                        className={styles.goalProgressFill}
                        style={{ width: `${goal.progress}%` }}
                      />
                    </div>
                    <div className={styles.goalTarget}>
                      Target: {new Date(goal.target_date).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Weekly Focus Widget */}
          <Card title="🌟 This Week's Focus" className={styles.weeklyFocusCard}>
            <div className={styles.weeklyFocus}>
              <div className={styles.focusHabit}>Habit 5: Seek First to Understand</div>
              <div className={styles.focusDescription}>
                40% of your findings relate to this habit
              </div>
              <Button variant="outline" className={styles.focusButton}>
                View Strategies
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}