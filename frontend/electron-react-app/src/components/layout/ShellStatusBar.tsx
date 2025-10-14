import { useMemo } from 'react';

import { useHealthStatus } from '../../hooks/useHealthStatus';
import { useSystemMetrics } from '../../hooks/useSystemMetrics';
import { useAppStore } from '../../store/useAppStore';
import { useTaskMonitor } from '../../features/analysis/hooks/useTaskMonitor';
import { StatusChip } from '../ui/StatusChip';

import styles from './ShellStatusBar.module.css';

export const ShellStatusBar = () => {
  const token = useAppStore((state) => state.auth.token);
  const healthQuery = useHealthStatus({ enabled: Boolean(token) });
  const metricsQuery = useSystemMetrics({ enabled: Boolean(token) });
  const tasksQuery = useTaskMonitor({ enabled: Boolean(token) });

  const taskSummary = useMemo(() => {
    const tasks = tasksQuery.data ? Object.values(tasksQuery.data) : [];
    const active = tasks.filter((task) => task.status !== 'completed' && task.status !== 'failed');
    return {
      active: active.length,
      total: tasks.length,
    };
  }, [tasksQuery.data]);

  const healthStatus = healthQuery.data?.status === 'ok' ? 'ready' : 'warning';
  const healthLabel = healthQuery.isLoading
    ? 'Checking...'
    : healthQuery.data?.status === 'ok'
      ? 'Connected'
      : 'Unavailable';

  const metricsLabel = metricsQuery.isLoading
    ? 'Collecting...'
    : metricsQuery.data
      ? `CPU ${Math.round(metricsQuery.data.cpuPercent)}% | RAM ${Math.round(metricsQuery.data.memoryPercent)}%`
      : 'Unavailable';
  const metricsVariant: 'ready' | 'warning' = metricsQuery.data ? 'ready' : 'warning';

  return (
    <footer className={styles.footer}>
      <div className={styles.section}>
        <span className={styles.label}>API Server</span>
        <StatusChip label={healthLabel} status={healthStatus} />
      </div>
      <div className={styles.section}>
        <span className={styles.label}>Tasks</span>
        <span className={styles.value}>
          {taskSummary.active} active | {taskSummary.total} total
        </span>
      </div>
      <div className={styles.sectionRight}>
        <span className={styles.label}>System</span>
        <StatusChip label={metricsLabel} status={metricsVariant} />
      </div>
    </footer>
  );
};
