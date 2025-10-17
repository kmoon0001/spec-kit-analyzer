import React, { useState } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { useMetaAnalytics } from '../hooks/useMetaAnalytics';
import { DisciplineChart } from '../components/DisciplineChart';
import { HabitsDistributionChart } from '../components/HabitsDistributionChart';
import { TrainingNeedsChart } from '../components/TrainingNeedsChart';
import styles from './MetaAnalyticsPage.module.css';

const DISCIPLINE_OPTIONS = ['All Disciplines', 'PT', 'OT', 'SLP'];

export default function MetaAnalyticsPage() {
  const [daysBack, setDaysBack] = useState(90);
  const [discipline, setDiscipline] = useState('All Disciplines');
  const [activeTab, setActiveTab] = useState('overview');

  const { data, isLoading, isError, refetch } = useMetaAnalytics(
    daysBack,
    discipline === 'All Disciplines' ? undefined : discipline
  );

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div>Loading organizational analytics...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className={styles.error}>
        <div>Failed to load analytics data</div>
        <Button onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  const renderOverviewTab = () => (
    <div className={styles.tabContent}>
      {/* Key Metrics */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Users</div>
          <div className={styles.metricValue}>{data?.organizational_metrics?.total_users || 0}</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Avg Compliance</div>
          <div className={styles.metricValue}>
            {data?.organizational_metrics?.avg_compliance_score?.toFixed(1) || '0.0'}%
          </div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Findings</div>
          <div className={styles.metricValue}>{data?.organizational_metrics?.total_findings || 0}</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Analyses</div>
          <div className={styles.metricValue}>{data?.organizational_metrics?.total_analyses || 0}</div>
        </div>
      </div>

      {/* Charts */}
      <div className={styles.chartsGrid}>
        <Card title="Performance by Discipline" className={styles.chartCard}>
          {data?.organizational_metrics?.discipline_breakdown && (
            <DisciplineChart disciplineData={data.organizational_metrics.discipline_breakdown} />
          )}
        </Card>

        <Card title="Top 5 Habits Distribution" className={styles.chartCard}>
          {data?.organizational_metrics?.team_habit_breakdown && (
            <HabitsDistributionChart habitsData={data.organizational_metrics.team_habit_breakdown} />
          )}
        </Card>
      </div>

      {/* Insights */}
      {data?.insights && data.insights.length > 0 && (
        <Card title="Key Insights" className={styles.insightsCard}>
          <div className={styles.insightsList}>
            {data.insights.map((insight, index) => (
              <div key={index} className={`${styles.insightItem} ${styles[insight.level]}`}>
                <div className={styles.insightTitle}>{insight.title}</div>
                <div className={styles.insightDescription}>{insight.description}</div>
                <div className={styles.insightRecommendation}>
                  <strong>Recommendation:</strong> {insight.recommendation}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );

  const renderTrainingTab = () => (
    <div className={styles.tabContent}>
      <Card title="Training Needs by Habit Area" className={styles.trainingChartCard}>
        {data?.training_needs && (
          <TrainingNeedsChart trainingNeeds={data.training_needs} />
        )}
      </Card>

      {data?.training_needs && data.training_needs.length > 0 && (
        <Card title="Top Training Recommendations" className={styles.trainingRecsCard}>
          <div className={styles.trainingRecommendations}>
            {data.training_needs.slice(0, 3).map((need, index) => (
              <div key={index} className={styles.trainingRec}>
                <div className={styles.trainingRecHeader}>
                  <div className={styles.trainingRecTitle}>{need.habit_name}</div>
                  <div className={`${styles.trainingRecPriority} ${styles[need.priority]}`}>
                    {need.priority.toUpperCase()}
                  </div>
                </div>
                <div className={styles.trainingRecStats}>
                  <span>{need.percentage_of_findings.toFixed(1)}% of findings</span>
                  <span>Affected users: {need.affected_users}</span>
                </div>
                <div className={styles.trainingRecFocus}>
                  <strong>Focus:</strong> {need.training_focus}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );

  const renderTrendsTab = () => (
    <div className={styles.tabContent}>
      <Card title="Team Performance Trends Over Time" className={styles.trendsCard}>
        {data?.team_trends && data.team_trends.length > 0 ? (
          <div className={styles.trendsChart}>
            {/* Simple trend visualization - could be enhanced with recharts */}
            <div className={styles.trendsTable}>
              <div className={styles.trendsHeader}>
                <div>Week</div>
                <div>Avg Compliance</div>
                <div>Total Findings</div>
              </div>
              {data.team_trends.map((trend, index) => (
                <div key={index} className={styles.trendsRow}>
                  <div>Week {trend.week}</div>
                  <div>{trend.avg_compliance_score.toFixed(1)}%</div>
                  <div>{trend.total_findings}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.noData}>No trend data available</div>
        )}
      </Card>
    </div>
  );

  const renderBenchmarksTab = () => (
    <div className={styles.tabContent}>
      <Card title="Team Compliance Score Percentiles" className={styles.benchmarksCard}>
        {data?.benchmarks ? (
          <div className={styles.benchmarksContent}>
            <div className={styles.benchmarksSummary}>
              <div className={styles.benchmarksTitle}>
                Benchmark Summary (based on {data.benchmarks.total_users_in_benchmark} users)
              </div>
            </div>

            <div className={styles.percentilesGrid}>
              <div className={styles.percentileCard}>
                <div className={styles.percentileLabel}>25th Percentile</div>
                <div className={styles.percentileValue}>
                  {data.benchmarks.compliance_score_percentiles.p25}%
                </div>
              </div>
              <div className={styles.percentileCard}>
                <div className={styles.percentileLabel}>50th Percentile (Median)</div>
                <div className={styles.percentileValue}>
                  {data.benchmarks.compliance_score_percentiles.p50}%
                </div>
              </div>
              <div className={styles.percentileCard}>
                <div className={styles.percentileLabel}>75th Percentile</div>
                <div className={styles.percentileValue}>
                  {data.benchmarks.compliance_score_percentiles.p75}%
                </div>
              </div>
              <div className={styles.percentileCard}>
                <div className={styles.percentileLabel}>90th Percentile</div>
                <div className={styles.percentileValue}>
                  {data.benchmarks.compliance_score_percentiles.p90}%
                </div>
              </div>
            </div>

            <div className={styles.benchmarksNote}>
              This data represents anonymous performance distribution across your organization.
            </div>
          </div>
        ) : (
          <div className={styles.noData}>No benchmark data available</div>
        )}
      </Card>
    </div>
  );

  return (
    <div className={styles.container}>
      {/* Header with Controls */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h2>📊 Organizational Analytics & Team Insights</h2>
          <div className={styles.controls}>
            <div className={styles.controlGroup}>
              <label>Analysis Period:</label>
              <input
                type="number"
                min="7"
                max="365"
                value={daysBack}
                onChange={(e) => setDaysBack(parseInt(e.target.value))}
                className={styles.daysInput}
              />
              <span>days</span>
            </div>

            <div className={styles.controlGroup}>
              <label>Discipline:</label>
              <select
                value={discipline}
                onChange={(e) => setDiscipline(e.target.value)}
                className={styles.disciplineSelect}
              >
                {DISCIPLINE_OPTIONS.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>

            <Button onClick={() => refetch()} variant="outline">
              Refresh Analytics
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'overview' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Team Overview
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'training' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('training')}
        >
          Training Needs
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'trends' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          Performance Trends
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'benchmarks' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('benchmarks')}
        >
          Benchmarks
        </button>
      </div>

      {/* Tab Content */}
      <div className={styles.content}>
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'training' && renderTrainingTab()}
        {activeTab === 'trends' && renderTrendsTab()}
        {activeTab === 'benchmarks' && renderBenchmarksTab()}
      </div>
    </div>
  );
}