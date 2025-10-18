import { useState, useEffect, useCallback } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { StatusChip } from '../../../components/ui/StatusChip';

import styles from './AdvancedAnalyticsPage.module.css';

interface AnalyticsData {
  complianceTrends: {
    dates: string[];
    overallScores: number[];
    frequencyScores: number[];
    goalScores: number[];
    progressScores: number[];
  };
  riskPredictions: {
    highRisk: number;
    mediumRisk: number;
    lowRisk: number;
    trends: string[];
  };
  teamMetrics: {
    totalDocuments: number;
    averageScore: number;
    disciplineBreakdown: {
      pt: number;
      ot: number;
      slp: number;
    };
  };
}

const TIME_RANGES = [
  { value: '7', label: 'Last 7 Days' },
  { value: '30', label: 'Last 30 Days' },
  { value: '90', label: 'Last 90 Days' },
  { value: '365', label: 'Last Year' }
];

const DISCIPLINE_FILTERS = [
  { value: 'all', label: 'All Disciplines' },
  { value: 'pt', label: 'Physical Therapy (PT)' },
  { value: 'ot', label: 'Occupational Therapy (OT)' },
  { value: 'slp', label: 'Speech-Language Pathology (SLP)' }
];

export default function AdvancedAnalyticsPage() {
  const [timeRange, setTimeRange] = useState('30');
  const [disciplineFilter, setDisciplineFilter] = useState('all');
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const generateMockData = useCallback((): AnalyticsData => {
    const days = parseInt(timeRange);
    const dates = Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i - 1));
      return date.toISOString().split('T')[0];
    });

    // Generate realistic compliance scores with upward trend
    const baseScore = 75 + Math.random() * 20;
    const overallScores = dates.map((_, i) => {
      const trend = i * 0.3;
      const noise = Math.random() * 10 - 5;
      return Math.min(100, Math.max(60, baseScore + trend + noise));
    });

    return {
      complianceTrends: {
        dates,
        overallScores,
        frequencyScores: overallScores.map(s => s + Math.random() * 10 - 5),
        goalScores: overallScores.map(s => s + Math.random() * 8 - 4),
        progressScores: overallScores.map(s => s + Math.random() * 12 - 6),
      },
      riskPredictions: {
        highRisk: Math.floor(Math.random() * 15) + 5,
        mediumRisk: Math.floor(Math.random() * 25) + 15,
        lowRisk: Math.floor(Math.random() * 40) + 40,
        trends: [
          'Goal documentation needs improvement',
          'Frequency tracking shows positive trend',
          'Progress notes require more detail',
          'Medical necessity documentation strong'
        ]
      },
      teamMetrics: {
        totalDocuments: Math.floor(Math.random() * 200) + 100,
        averageScore: Math.random() * 20 + 75,
        disciplineBreakdown: {
          pt: Math.floor(Math.random() * 50) + 30,
          ot: Math.floor(Math.random() * 40) + 20,
          slp: Math.floor(Math.random() * 30) + 15,
        }
      }
    };
  }, [timeRange]);

  const refreshAnalytics = useCallback(async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setAnalyticsData(generateMockData());
      setIsLoading(false);
    }, 1000);
  }, [generateMockData]);

  useEffect(() => {
    refreshAnalytics();
  }, [timeRange, disciplineFilter, refreshAnalytics]);

  return (
    <div className={styles.wrapper}>
      {/* Header with Controls */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>📊 Advanced Analytics & Predictive Insights</h1>
          <p className={styles.subtitle}>
            Comprehensive compliance analytics with predictive insights and team performance metrics
          </p>
        </div>

        <div className={styles.controls}>
          <div className={styles.controlGroup}>
            <label className={styles.controlLabel}>Time Range:</label>
            <select
              className={styles.controlSelect}
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
            >
              {TIME_RANGES.map(range => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.controlGroup}>
            <label className={styles.controlLabel}>Discipline:</label>
            <select
              className={styles.controlSelect}
              value={disciplineFilter}
              onChange={(e) => setDisciplineFilter(e.target.value)}
            >
              {DISCIPLINE_FILTERS.map(filter => (
                <option key={filter.value} value={filter.value}>
                  {filter.label}
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

      {/* Team Overview Metrics */}
      <div className={styles.metricsGrid}>
        <Card title="Team Overview" subtitle="Key Performance Indicators">
          <div className={styles.metricCards}>
            <div className={styles.metricCard}>
              <div className={styles.metricValue}>
                {analyticsData?.teamMetrics.totalDocuments || 0}
              </div>
              <div className={styles.metricLabel}>Total Documents</div>
            </div>
            <div className={styles.metricCard}>
              <div className={styles.metricValue}>
                {analyticsData?.teamMetrics.averageScore.toFixed(1) || '0.0'}%
              </div>
              <div className={styles.metricLabel}>Average Compliance</div>
            </div>
            <div className={styles.metricCard}>
              <div className={styles.metricValue}>
                {analyticsData?.riskPredictions.lowRisk || 0}%
              </div>
              <div className={styles.metricLabel}>Low Risk Documents</div>
            </div>
          </div>
        </Card>

        <Card title="Discipline Breakdown" subtitle="Document distribution by therapy discipline">
          <div className={styles.disciplineBreakdown}>
            <div className={styles.disciplineItem}>
              <div className={styles.disciplineLabel}>Physical Therapy</div>
              <div className={styles.disciplineBar}>
                <div
                  className={styles.disciplineFill}
                  style={{ width: `${analyticsData?.teamMetrics.disciplineBreakdown.pt || 0}%` }}
                />
              </div>
              <div className={styles.disciplineValue}>
                {analyticsData?.teamMetrics.disciplineBreakdown.pt || 0}%
              </div>
            </div>
            <div className={styles.disciplineItem}>
              <div className={styles.disciplineLabel}>Occupational Therapy</div>
              <div className={styles.disciplineBar}>
                <div
                  className={styles.disciplineFill}
                  style={{ width: `${analyticsData?.teamMetrics.disciplineBreakdown.ot || 0}%` }}
                />
              </div>
              <div className={styles.disciplineValue}>
                {analyticsData?.teamMetrics.disciplineBreakdown.ot || 0}%
              </div>
            </div>
            <div className={styles.disciplineItem}>
              <div className={styles.disciplineLabel}>Speech-Language Pathology</div>
              <div className={styles.disciplineBar}>
                <div
                  className={styles.disciplineFill}
                  style={{ width: `${analyticsData?.teamMetrics.disciplineBreakdown.slp || 0}%` }}
                />
              </div>
              <div className={styles.disciplineValue}>
                {analyticsData?.teamMetrics.disciplineBreakdown.slp || 0}%
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Risk Analysis */}
      <div className={styles.riskAnalysis}>
        <Card title="Risk Analysis" subtitle="Document risk distribution and trends">
          <div className={styles.riskGrid}>
            <div className={styles.riskCard}>
              <div className={styles.riskValue} style={{ color: 'var(--color-error)' }}>
                {analyticsData?.riskPredictions.highRisk || 0}%
              </div>
              <div className={styles.riskLabel}>High Risk</div>
              <StatusChip label="Requires Attention" status="warning" />
            </div>
            <div className={styles.riskCard}>
              <div className={styles.riskValue} style={{ color: 'var(--color-warning)' }}>
                {analyticsData?.riskPredictions.mediumRisk || 0}%
              </div>
              <div className={styles.riskLabel}>Medium Risk</div>
              <StatusChip label="Monitor Closely" status="warming" />
            </div>
            <div className={styles.riskCard}>
              <div className={styles.riskValue} style={{ color: 'var(--color-success)' }}>
                {analyticsData?.riskPredictions.lowRisk || 0}%
              </div>
              <div className={styles.riskLabel}>Low Risk</div>
              <StatusChip label="Compliant" status="ready" />
            </div>
          </div>

          <div className={styles.riskTrends}>
            <h4>Key Trends & Insights:</h4>
            <ul className={styles.trendsList}>
              {analyticsData?.riskPredictions.trends.map((trend, index) => (
                <li key={index} className={styles.trendItem}>
                  <span className={styles.trendBullet}>•</span>
                  {trend}
                </li>
              ))}
            </ul>
          </div>
        </Card>
      </div>

      {/* Compliance Trends Chart */}
      <Card title="Compliance Trends" subtitle="Performance over time">
        <div className={styles.chartContainer}>
          <div className={styles.chartPlaceholder}>
            <div className={styles.chartIcon}>📈</div>
            <h3>Compliance Trend Chart</h3>
            <p>Interactive chart showing compliance scores over the selected time period</p>
            <div className={styles.chartLegend}>
              <div className={styles.legendItem}>
                <div className={styles.legendColor} style={{ backgroundColor: 'var(--color-primary)' }} />
                Overall Compliance
              </div>
              <div className={styles.legendItem}>
                <div className={styles.legendColor} style={{ backgroundColor: 'var(--color-success)' }} />
                Goal Documentation
              </div>
              <div className={styles.legendItem}>
                <div className={styles.legendColor} style={{ backgroundColor: 'var(--color-warning)' }} />
                Progress Tracking
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Training Needs */}
      <Card title="Training Needs Identification" subtitle="Areas requiring team development">
        <div className={styles.trainingNeeds}>
          <div className={styles.trainingItem}>
            <div className={styles.trainingIcon}>🎯</div>
            <div className={styles.trainingContent}>
              <h4>Goal Documentation</h4>
              <p>23% of documents lack specific, measurable goals</p>
              <StatusChip label="High Priority" status="warning" />
            </div>
          </div>
          <div className={styles.trainingItem}>
            <div className={styles.trainingIcon}>📝</div>
            <div className={styles.trainingContent}>
              <h4>Progress Note Detail</h4>
              <p>18% of progress notes need more clinical detail</p>
              <StatusChip label="Medium Priority" status="warming" />
            </div>
          </div>
          <div className={styles.trainingItem}>
            <div className={styles.trainingIcon}>⚕️</div>
            <div className={styles.trainingContent}>
              <h4>Medical Necessity</h4>
              <p>12% of documents require stronger medical necessity justification</p>
              <StatusChip label="Low Priority" status="ready" />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}