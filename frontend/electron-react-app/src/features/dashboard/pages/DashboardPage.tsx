import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { Card } from '../../../components/ui/Card';
import { StatusChip } from '../../../components/ui/StatusChip';
import { useAppStore } from '../../../store/useAppStore';
import { useTaskMonitor } from '../../analysis/hooks/useTaskMonitor';
import { fetchDashboardOverview, fetchDashboardStatistics } from '../api';

import styles from './DashboardPage.module.css';

type ScoreCard = {
  label: string;
  value: string;
  hint: string;
  tone: 'ready' | 'warming' | 'offline' | 'warning';
};

type ComplianceRow = {
  name: string;
  score: number;
  count: number;
};

type TaskRow = {
  id: string;
  document: string;
  progress: number;
  status: string;
};

type AiHealthRow = {
  component: string;
  status: 'ready' | 'warming' | 'warning' | 'offline';
  details: string;
};

const scoreCardFallback: ScoreCard[] = [
  {
    label: 'Average Compliance',
    value: '--',
    hint: 'Awaiting data',
    tone: 'warning',
  },
  {
    label: 'Documents Analyzed',
    value: '--',
    hint: 'Awaiting data',
    tone: 'warming',
  },
  {
    label: 'Tracked Disciplines',
    value: '--',
    hint: 'Awaiting data',
    tone: 'offline',
  },
];

const toTitleCase = (value: string) =>
  value
    .split(/[_\s]+/g)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');

const mapHealthStatus = (label: string) => {
  const normalized = label.toLowerCase();
  if (normalized.includes('healthy') || normalized.includes('ready')) {
    return 'ready';
  }
  if (normalized.includes('degraded') || normalized.includes('warning')) {
    return 'warning';
  }
  if (normalized.includes('loading') || normalized.includes('warming')) {
    return 'warming';
  }
  return 'offline';
};

export default function DashboardPage() {
  const token = useAppStore((state) => state.auth.token);

  const statsQuery = useQuery({
    queryKey: ['dashboard-statistics'],
    queryFn: fetchDashboardStatistics,
    enabled: Boolean(token),
    staleTime: 15_000,
  });

  const overviewQuery = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: fetchDashboardOverview,
    enabled: Boolean(token),
    staleTime: 15_000,
  });

  const taskQuery = useTaskMonitor({ enabled: Boolean(token) });

  const scoreCards = useMemo<ScoreCard[]>(() => {
    const stats = statsQuery.data;
    if (!stats) {
      return scoreCardFallback;
    }
    const compliant = Number.isFinite(stats.overallComplianceScore)
      ? `${stats.overallComplianceScore.toFixed(1)}%`
      : '--';
    const documents = stats.totalDocumentsAnalyzed.toLocaleString();
    const categories = Object.keys(stats.complianceByCategory ?? {}).length;

    return [
      {
        label: 'Average Compliance',
        value: compliant,
        hint: stats.error ? 'API reported an error' : 'Updated recently',
        tone: stats.error ? 'warning' : 'ready',
      },
      {
        label: 'Documents Analyzed',
        value: documents,
        hint: 'Historical reports ingested',
        tone: documents === '0' ? 'warming' : 'ready',
      },
      {
        label: 'Tracked Disciplines',
        value: categories.toString(),
        hint: 'Distinct document types scored',
        tone: categories === 0 ? 'warming' : 'ready',
      },
    ];
  }, [statsQuery.data]);

  const complianceRows = useMemo<ComplianceRow[]>(() => {
    const stats = statsQuery.data;
    if (!stats) {
      return [];
    }
    return Object.entries(stats.complianceByCategory ?? {}).map(([name, values]) => ({
      name: toTitleCase(name),
      score: Math.round(values.average_score ?? 0),
      count: values.document_count ?? 0,
    }));
  }, [statsQuery.data]);

  const tasks = useMemo<TaskRow[]>(() => {
    const entries = taskQuery.data ? Object.entries(taskQuery.data) : [];
    return entries.map(([id, task]) => ({
      id,
      document: task.filename ?? 'Pending document name',
      progress: task.progress ?? 0,
      status: task.status_message ?? task.status ?? 'pending',
    }));
  }, [taskQuery.data]);

  const aiHealthRows = useMemo<AiHealthRow[]>(() => {
    const aiHealth = overviewQuery.data?.aiHealth ?? {};
    return Object.entries(aiHealth).map(([component, payload]) => ({
      component: toTitleCase(component),
      status: mapHealthStatus(payload.status),
      details: payload.details,
    }));
  }, [overviewQuery.data?.aiHealth]);

  const systemMetrics = overviewQuery.data?.systemMetrics;

  return (
    <div className={styles.dashboard}>
      <header>
        <h2>Compliance Intelligence Dashboard</h2>
        <p>
          Mirrors the PySide dashboard tab with live metrics from the FastAPI services powering the Electron shell.
        </p>
      </header>

      <section className={styles.metricsRow}>
        {scoreCards.map((card) => (
          <Card key={card.label}>
            <span className={styles.metricLabel}>{card.label}</span>
            <span className={styles.metricValue}>{card.value}</span>
            <StatusChip label={card.hint} status={card.tone} />
          </Card>
        ))}
      </section>

      <section className={styles.gridTwo}>
        <Card title="Discipline Compliance" subtitle="Averages per document type from AnalysisReport records">
          {statsQuery.isLoading && <p className={styles.helperText}>Loading compliance statistics...</p>}
          {statsQuery.isError && <p className={styles.errorText}>Unable to load dashboard statistics. Check API status.</p>}
          {!statsQuery.isLoading && !statsQuery.isError && complianceRows.length === 0 && (
            <p className={styles.helperText}>No analyzed documents yet. Run an analysis to populate this chart.</p>
          )}
          {complianceRows.length > 0 && (
            <ul className={styles.listPlain}>
              {complianceRows.map((row) => (
                <li key={row.name}>
                  <span>{row.name}</span>
                  <div className={styles.progressBar}>
                    <div style={{ width: `${Math.min(row.score, 100)}%` }} />
                  </div>
                  <span className={styles.progressValue}>{row.score}% | {row.count} docs</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Mission Control Queue" subtitle="Latest analysis tasks from the shared registry">
          {taskQuery.isFetching && <p className={styles.helperText}>Refreshing active tasks...</p>}
          {tasks.length === 0 && !taskQuery.isFetching && (
            <p className={styles.helperText}>No active tasks detected. Launch an analysis to populate this queue.</p>
          )}
          {tasks.length > 0 && (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Progress</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((row) => (
                  <tr key={row.id}>
                    <td>{row.document}</td>
                    <td>{`${Math.round(row.progress)}%`}</td>
                    <td>{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </section>

      <section className={styles.gridTwo}>
        <Card title="AI Operations" subtitle="Status reported by the FastAPI dashboard overview endpoint">
          {overviewQuery.isLoading && <p className={styles.helperText}>Checking AI component health...</p>}
          {overviewQuery.isError && (
            <p className={styles.errorText}>Unable to reach the AI health endpoint.</p>
          )}
          {aiHealthRows.length === 0 && !overviewQuery.isLoading && !overviewQuery.isError && (
            <p className={styles.helperText}>AI health details will appear once monitoring finishes its first pass.</p>
          )}
          {aiHealthRows.length > 0 && (
            <ul className={styles.flagList}>
              {aiHealthRows.map((row) => (
                <li key={row.component}>
                  <StatusChip label={row.component} status={row.status} />
                  <span>{row.details}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="System Observability" subtitle="Resource usage reported by dashboard overview">
          {systemMetrics ? (
            <div className={styles.placeholder}>
              CPU Load: {Math.round(systemMetrics.cpu_usage ?? 0)}% | Memory: {Math.round(systemMetrics.memory_usage ?? 0)}%
            </div>
          ) : (
            <div className={styles.placeholder}>
              System metrics will appear after the first polling cycle or when the API exposes telemetry.
            </div>
          )}
        </Card>
      </section>
    </div>
  );
}
