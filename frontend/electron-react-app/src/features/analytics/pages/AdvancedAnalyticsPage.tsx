import React, { useState } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { useAdvancedAnalytics } from '../hooks/useAdvancedAnalytics';
import { MetricCard } from '../components/MetricCard';
import { ComplianceChart } from '../components/ComplianceChart';
import { CategoryBreakdown } from '../components/CategoryBreakdown';
import { RiskFactorWidget } from '../components/RiskFactorWidget';
import { RecommendationWidget } from '../components/RecommendationWidget';
import { BenchmarkComparison } from '../components/BenchmarkComparison';
import { RiskGauge } from '../components/RiskGauge';
import styles from './AdvancedAnalyticsPage.module.css';

const TIME_RANGES = ['Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'Last Year'];

export default function AdvancedAnalyticsPage() {
  const [timeRange, setTimeRange] = useState('Last 30 Days');
  const [activeTab, setActiveTab] = useState('trends');

  const { analytics, predictive, benchmarks, isLoading, isError, refetch } = useAdvancedAnalytics(timeRange);

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div>Loading advanced analytics...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className={styles.error}>
        <div>Failed to load analytics data</div>
        <Button onClick={refetch}>Retry</Button>
      </div>
    );
  }

  const renderTrendsTab = () => (
    <div className={styles.tabContent}>
      {/* Key Metrics Cards */}
      <div className={styles.metricsGrid}>
        <MetricCard
          title="Overall Compliance"
          value={analytics?.key_metrics?.overall_compliance ? `${analytics.key_metrics.overall_compliance}%` : '--'}
          change="↑ 12.4%"
          color="#28a745"
        />
        <MetricCard
          title="Documentation Quality"
          value={analytics?.key_metrics?.documentation_quality ? `${analytics.key_metrics.documentation_quality}%` : '--'}
          change="↑ 8.7%"
          color="#007acc"
        />
        <MetricCard
          title="Risk Score"
          value={analytics?.key_metrics?.risk_score ? `${analytics.key_metrics.risk_score}%` : '--'}
          change="↓ 23.1%"
          color="#dc3545"
        />
        <MetricCard
          title="Efficiency Index"
          value={analytics?.key_metrics?.efficiency_index ? `${analytics.key_metrics.efficiency_index}%` : '--'}
          change="↑ 15.3%"
          color="#ffc107"
        />
      </div>

      {/* Charts Section */}
      <div className={styles.chartsLayout}>
        <div className={styles.chartContainer}>
          {analytics?.compliance_trends && (
            <ComplianceChart
              data={analytics.compliance_trends}
              title="Compliance Trends Over Time"
            />
          )}
        </div>
        <div className={styles.breakdownContainer}>
          {analytics?.category_breakdown && (
            <CategoryBreakdown categories={analytics.category_breakdown} />
          )}
        </div>
      </div>
    </div>
  );

  const renderPredictiveTab = () => (
    <div className={styles.tabContent}>
      {/* Prediction Summary */}
      <Card title="🔮 Compliance Forecast" className={styles.forecastCard}>
        <div className={styles.predictionsGrid}>
          <div className={styles.prediction}>
            <div className={styles.predictionPeriod}>30 Days</div>
            <div className={styles.predictionScore}>
              {predictive?.compliance_forecast?.['30_days'] || '--'}%
            </div>
            <div className={styles.predictionConfidence}>High Confidence</div>
          </div>
          <div className={styles.prediction}>
            <div className={styles.predictionPeriod}>60 Days</div>
            <div className={styles.predictionScore}>
              {predictive?.compliance_forecast?.['60_days'] || '--'}%
            </div>
            <div className={styles.predictionConfidence}>Medium Confidence</div>
          </div>
          <div className={styles.prediction}>
            <div className={styles.predictionPeriod}>90 Days</div>
            <div className={styles.predictionScore}>
              {predictive?.compliance_forecast?.['90_days'] || '--'}%
            </div>
            <div className={styles.predictionConfidence}>Medium Confidence</div>
          </div>
        </div>
      </Card>

      {/* Risk Factors */}
      <Card title="⚠️ Risk Factors Analysis" className={styles.riskFactorsCard}>
        {predictive?.audit_risk?.factors?.map((factor, index) => (
          <RiskFactorWidget key={index} factor={factor} />
        ))}
      </Card>

      {/* Recommendations */}
      <Card title="💡 AI-Powered Recommendations" className={styles.recommendationsCard}>
        {predictive?.recommendations?.map((rec, index) => (
          <RecommendationWidget key={index} recommendation={rec} />
        ))}
      </Card>
    </div>
  );

  const renderBenchmarksTab = () => (
    <div className={styles.tabContent}>
      {/* Performance Ranking */}
      <Card title="📊 Industry Benchmarking" className={styles.benchmarkCard}>
        <div className={styles.rankingHeader}>
          🏆 Your Performance Ranking: {benchmarks?.percentile_ranking || '--'}th Percentile
        </div>

        <div className={styles.benchmarkComparisons}>
          <BenchmarkComparison
            name="Overall Compliance"
            yourScore={benchmarks?.your_performance?.overall_compliance || 0}
            industryAvg={benchmarks?.industry_averages?.overall_compliance || 0}
            topPerformer={benchmarks?.top_performers?.overall_compliance || 0}
          />
          <BenchmarkComparison
            name="Frequency Documentation"
            yourScore={benchmarks?.your_performance?.frequency_documentation || 0}
            industryAvg={benchmarks?.industry_averages?.frequency_documentation || 0}
            topPerformer={benchmarks?.top_performers?.frequency_documentation || 0}
          />
          <BenchmarkComparison
            name="Goal Specificity"
            yourScore={benchmarks?.your_performance?.goal_specificity || 0}
            industryAvg={benchmarks?.industry_averages?.goal_specificity || 0}
            topPerformer={benchmarks?.top_performers?.goal_specificity || 0}
          />
          <BenchmarkComparison
            name="Progress Tracking"
            yourScore={benchmarks?.your_performance?.progress_tracking || 0}
            industryAvg={benchmarks?.industry_averages?.progress_tracking || 0}
            topPerformer={benchmarks?.top_performers?.progress_tracking || 0}
          />
        </div>
      </Card>
    </div>
  );

  const renderRiskAssessmentTab = () => (
    <div className={styles.tabContent}>
      {/* Risk Overview */}
      <Card title="🎯 Risk Assessment Overview" className={styles.riskOverviewCard}>
        <RiskGauge riskScore={predictive?.audit_risk?.current || 0} />
      </Card>

      {/* Risk Mitigation Strategies */}
      <Card title="🛡️ Risk Mitigation Strategies" className={styles.mitigationCard}>
        <div className={styles.strategiesGrid}>
          <div className={styles.strategySection}>
            <h4>Immediate Actions (Next 7 Days)</h4>
            <ul>
              <li>Review and update frequency documentation templates</li>
              <li>Conduct spot-check of recent documentation</li>
              <li>Schedule team meeting on compliance best practices</li>
            </ul>
          </div>
          <div className={styles.strategySection}>
            <h4>Short-term Improvements (Next 30 Days)</h4>
            <ul>
              <li>Implement SMART goals training program</li>
              <li>Create documentation quality checklist</li>
              <li>Establish peer review process</li>
            </ul>
          </div>
          <div className={styles.strategySection}>
            <h4>Long-term Initiatives (Next 90 Days)</h4>
            <ul>
              <li>Deploy automated compliance checking tools</li>
              <li>Develop comprehensive training curriculum</li>
              <li>Establish continuous monitoring system</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h2>📊 Advanced Analytics & Predictive Insights</h2>
          <div className={styles.headerControls}>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className={styles.timeRangeSelect}
            >
              {TIME_RANGES.map(range => (
                <option key={range} value={range}>{range}</option>
              ))}
            </select>
            <Button onClick={refetch} variant="outline">
              🔄 Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'trends' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          📈 Trends
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'predictive' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('predictive')}
        >
          🔮 Predictive
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'benchmarks' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('benchmarks')}
        >
          🏆 Benchmarks
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'risk' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('risk')}
        >
          🛡️ Risk Assessment
        </button>
      </div>

      {/* Tab Content */}
      <div className={styles.content}>
        {activeTab === 'trends' && renderTrendsTab()}
        {activeTab === 'predictive' && renderPredictiveTab()}
        {activeTab === 'benchmarks' && renderBenchmarksTab()}
        {activeTab === 'risk' && renderRiskAssessmentTab()}
      </div>
    </div>
  );
}