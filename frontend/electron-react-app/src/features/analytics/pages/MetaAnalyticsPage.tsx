import { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { StatusChip } from '../../../components/ui/StatusChip';

import styles from './MetaAnalyticsPage.module.css';

interface TeamMetrics {
  totalDocuments: number;
  averageCompliance: number;
  teamSize: number;
  activeUsers: number;
  documentsThisWeek: number;
  complianceTrend: 'up' | 'down' | 'stable';
}

interface DisciplineMetrics {
  pt: {
    documents: number;
    averageScore: number;
    complianceRate: number;
  };
  ot: {
    documents: number;
    averageScore: number;
    complianceRate: number;
  };
  slp: {
    documents: number;
    averageScore: number;
    complianceRate: number;
  };
}

interface TrainingNeeds {
  highPriority: string[];
  mediumPriority: string[];
  lowPriority: string[];
}

const TIME_PERIODS = [
  { value: '7', label: 'Last 7 Days' },
  { value: '30', label: 'Last 30 Days' },
  { value: '90', label: 'Last 90 Days' },
  { value: '365', label: 'Last Year' }
];

export default function MetaAnalyticsPage() {
  const [timePeriod, setTimePeriod] = useState('30');
  const [teamMetrics, setTeamMetrics] = useState<TeamMetrics | null>(null);
  const [disciplineMetrics, setDisciplineMetrics] = useState<DisciplineMetrics | null>(null);
  const [trainingNeeds, setTrainingNeeds] = useState<TrainingNeeds | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Mock data generation
  const generateMockData = () => {
    const baseCompliance = 75 + Math.random() * 20;

    setTeamMetrics({
      totalDocuments: Math.floor(Math.random() * 500) + 200,
      averageCompliance: baseCompliance,
      teamSize: Math.floor(Math.random() * 20) + 10,
      activeUsers: Math.floor(Math.random() * 15) + 8,
      documentsThisWeek: Math.floor(Math.random() * 50) + 20,
      complianceTrend: Math.random() > 0.5 ? 'up' : 'stable'
    });

    setDisciplineMetrics({
      pt: {
        documents: Math.floor(Math.random() * 200) + 100,
        averageScore: baseCompliance + Math.random() * 10 - 5,
        complianceRate: 85 + Math.random() * 10
      },
      ot: {
        documents: Math.floor(Math.random() * 150) + 75,
        averageScore: baseCompliance + Math.random() * 8 - 4,
        complianceRate: 80 + Math.random() * 15
      },
      slp: {
        documents: Math.floor(Math.random() * 100) + 50,
        averageScore: baseCompliance + Math.random() * 12 - 6,
        complianceRate: 88 + Math.random() * 8
      }
    });

    setTrainingNeeds({
      highPriority: [
        'Goal documentation specificity training',
        'Medical necessity justification workshops',
        'Progress note detail enhancement'
      ],
      mediumPriority: [
        'Frequency tracking best practices',
        'Outcome measurement documentation',
        'Interdisciplinary collaboration protocols'
      ],
      lowPriority: [
        'Documentation formatting standards',
        'Electronic health record optimization',
        'Quality assurance processes'
      ]
    });
  };

  const refreshAnalytics = async () => {
    setIsLoading(true);
    setTimeout(() => {
      generateMockData();
      setIsLoading(false);
    }, 1000);
  };

  useEffect(() => {
    generateMockData();
  }, [timePeriod]);

  return (
    <div className={styles.wrapper}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>👥 Team Analytics & Organizational Insights</h1>
          <p className={styles.subtitle}>
            Comprehensive team performance metrics, training needs identification, and organizational benchmarking
          </p>
        </div>

        <div className={styles.controls}>
          <div className={styles.controlGroup}>
            <label className={styles.controlLabel}>Analysis Period:</label>
            <select
              className={styles.controlSelect}
              value={timePeriod}
              onChange={(e) => setTimePeriod(e.target.value)}
            >
              {TIME_PERIODS.map(period => (
                <option key={period.value} value={period.value}>
                  {period.label}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="primary"
            onClick={refreshAnalytics}
            disabled={isLoading}
          >
            {isLoading ? '🔄 Refreshing...' : '🔄 Refresh Analytics'}
          </Button>
        </div>
      </div>

      {/* Team Overview */}
      <div className={styles.overviewGrid}>
        <Card title="Team Overview" subtitle="Key organizational metrics">
          <div className={styles.metricsGrid}>
            <div className={styles.metricItem}>
              <div className={styles.metricValue}>
                {teamMetrics?.totalDocuments || 0}
              </div>
              <div className={styles.metricLabel}>Total Documents</div>
            </div>
            <div className={styles.metricItem}>
              <div className={styles.metricValue}>
                {teamMetrics?.averageCompliance.toFixed(1) || '0.0'}%
              </div>
              <div className={styles.metricLabel}>Avg. Compliance</div>
            </div>
            <div className={styles.metricItem}>
              <div className={styles.metricValue}>
                {teamMetrics?.teamSize || 0}
              </div>
              <div className={styles.metricLabel}>Team Size</div>
            </div>
            <div className={styles.metricItem}>
              <div className={styles.metricValue}>
                {teamMetrics?.activeUsers || 0}
              </div>
              <div className={styles.metricLabel}>Active Users</div>
            </div>
          </div>

          <div className={styles.trendIndicator}>
            <div className={styles.trendLabel}>Compliance Trend:</div>
            <StatusChip
              label={teamMetrics?.complianceTrend === 'up' ? '📈 Improving' :
                teamMetrics?.complianceTrend === 'down' ? '📉 Declining' : '➡️ Stable'}
              status={teamMetrics?.complianceTrend === 'up' ? 'ready' :
                teamMetrics?.complianceTrend === 'down' ? 'warning' : 'warming'}
            />
          </div>
        </Card>

        <Card title="Activity Summary" subtitle="Recent team activity">
          <div className={styles.activitySummary}>
            <div className={styles.activityItem}>
              <div className={styles.activityIcon}>📄</div>
              <div className={styles.activityContent}>
                <div className={styles.activityValue}>
                  {teamMetrics?.documentsThisWeek || 0}
                </div>
                <div className={styles.activityLabel}>Documents This Week</div>
              </div>
            </div>
            <div className={styles.activityItem}>
              <div className={styles.activityIcon}>👥</div>
              <div className={styles.activityContent}>
                <div className={styles.activityValue}>
                  {teamMetrics?.activeUsers || 0}/{teamMetrics?.teamSize || 0}
                </div>
                <div className={styles.activityLabel}>Active Team Members</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Discipline Performance */}
      <Card title="Discipline Performance Comparison" subtitle="Performance metrics by therapy discipline">
        <div className={styles.disciplineComparison}>
          {disciplineMetrics && Object.entries(disciplineMetrics).map(([discipline, metrics]) => (
            <div key={discipline} className={styles.disciplineCard}>
              <div className={styles.disciplineHeader}>
                <h3 className={styles.disciplineTitle}>
                  {discipline.toUpperCase()}
                </h3>
                <StatusChip
                  label={`${metrics.complianceRate.toFixed(1)}% Compliant`}
                  status={metrics.complianceRate > 85 ? 'ready' :
                    metrics.complianceRate > 75 ? 'warming' : 'warning'}
                />
              </div>

              <div className={styles.disciplineMetrics}>
                <div className={styles.disciplineMetric}>
                  <div className={styles.disciplineMetricValue}>
                    {metrics.documents}
                  </div>
                  <div className={styles.disciplineMetricLabel}>Documents</div>
                </div>
                <div className={styles.disciplineMetric}>
                  <div className={styles.disciplineMetricValue}>
                    {metrics.averageScore.toFixed(1)}%
                  </div>
                  <div className={styles.disciplineMetricLabel}>Avg. Score</div>
                </div>
              </div>

              <div className={styles.disciplineBar}>
                <div
                  className={styles.disciplineBarFill}
                  style={{ width: `${metrics.complianceRate}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Training Needs Analysis */}
      <div className={styles.trainingGrid}>
        <Card title="High Priority Training Needs" subtitle="Immediate attention required">
          <div className={styles.trainingList}>
            {trainingNeeds?.highPriority.map((need, index) => (
              <div key={index} className={styles.trainingItem}>
                <div className={styles.trainingIcon}>🚨</div>
                <div className={styles.trainingText}>{need}</div>
                <StatusChip label="High Priority" status="warning" />
              </div>
            ))}
          </div>
        </Card>

        <Card title="Medium Priority Training Needs" subtitle="Schedule for upcoming sessions">
          <div className={styles.trainingList}>
            {trainingNeeds?.mediumPriority.map((need, index) => (
              <div key={index} className={styles.trainingItem}>
                <div className={styles.trainingIcon}>⚠️</div>
                <div className={styles.trainingText}>{need}</div>
                <StatusChip label="Medium Priority" status="warming" />
              </div>
            ))}
          </div>
        </Card>

        <Card title="Low Priority Training Needs" subtitle="Long-term development goals">
          <div className={styles.trainingList}>
            {trainingNeeds?.lowPriority.map((need, index) => (
              <div key={index} className={styles.trainingItem}>
                <div className={styles.trainingIcon}>💡</div>
                <div className={styles.trainingText}>{need}</div>
                <StatusChip label="Low Priority" status="ready" />
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Benchmarking */}
      <Card title="Industry Benchmarking" subtitle="Compare performance against industry standards">
        <div className={styles.benchmarkGrid}>
          <div className={styles.benchmarkItem}>
            <div className={styles.benchmarkLabel}>Medicare Compliance Rate</div>
            <div className={styles.benchmarkValue}>
              {teamMetrics?.averageCompliance.toFixed(1) || '0.0'}%
            </div>
            <div className={styles.benchmarkComparison}>
              <span className={styles.benchmarkIndustry}>Industry Avg: 78.5%</span>
              <StatusChip
                label={teamMetrics && teamMetrics.averageCompliance > 78.5 ? 'Above Average' : 'Below Average'}
                status={teamMetrics && teamMetrics.averageCompliance > 78.5 ? 'ready' : 'warning'}
              />
            </div>
          </div>

          <div className={styles.benchmarkItem}>
            <div className={styles.benchmarkLabel}>Documentation Volume</div>
            <div className={styles.benchmarkValue}>
              {teamMetrics?.documentsThisWeek || 0}/week
            </div>
            <div className={styles.benchmarkComparison}>
              <span className={styles.benchmarkIndustry}>Industry Avg: 35/week</span>
              <StatusChip
                label={teamMetrics && teamMetrics.documentsThisWeek > 35 ? 'High Volume' : 'Standard Volume'}
                status={teamMetrics && teamMetrics.documentsThisWeek > 35 ? 'ready' : 'warming'}
              />
            </div>
          </div>

          <div className={styles.benchmarkItem}>
            <div className={styles.benchmarkLabel}>Team Efficiency</div>
            <div className={styles.benchmarkValue}>
              {teamMetrics ? Math.round(teamMetrics.totalDocuments / teamMetrics.teamSize) : 0}
            </div>
            <div className={styles.benchmarkComparison}>
              <span className={styles.benchmarkIndustry}>Industry Avg: 25 docs/person</span>
              <StatusChip
                label={teamMetrics && (teamMetrics.totalDocuments / teamMetrics.teamSize) > 25 ? 'High Efficiency' : 'Standard Efficiency'}
                status={teamMetrics && (teamMetrics.totalDocuments / teamMetrics.teamSize) > 25 ? 'ready' : 'warming'}
              />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}