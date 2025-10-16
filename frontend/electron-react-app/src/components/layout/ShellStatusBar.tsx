import { useMemo } from 'react';

import { useHealthStatus } from '../../hooks/useHealthStatus';
import { useSystemMetrics } from '../../hooks/useSystemMetrics';
import { useAppStore } from '../../store/useAppStore';
import { useDiagnosticsStore } from '../../store/useDiagnosticsStore';
import { NetworkStatus, useNetworkStore } from '../../store/useNetworkStore';
import { useTaskMonitor } from '../../features/analysis/hooks/useTaskMonitor';
import { StatusChip } from '../ui/StatusChip';

import styles from './ShellStatusBar.module.css';

const NETWORK_LABELS: Record<NetworkStatus, string> = {
  idle: 'Initializing...',
  online: 'Stable',
  degraded: 'Network recovery...',
  offline: 'Offline',
};

const NETWORK_VARIANTS: Record<NetworkStatus, 'ready' | 'warming' | 'warning' | 'offline'> = {
  idle: 'warming',
  online: 'ready',
  degraded: 'warning',
  offline: 'offline',
};

const truncate = (value: string, max = 48) => (value.length > max ? `${value.slice(0, max - 3)}...` : value);

export const ShellStatusBar = () => {
  const token = useAppStore((state) => state.auth.token);
  const healthQuery = useHealthStatus({ enabled: Boolean(token) });
  const metricsQuery = useSystemMetrics({ enabled: Boolean(token) });
  const tasksQuery = useTaskMonitor({ enabled: Boolean(token) });
  const networkState = useNetworkStore((state) => ({
    status: state.status,
    lastError: state.lastError,
  }));
  const diagnosticsState = useDiagnosticsStore((state) => ({
    count: state.events.length,
    lastEvent: state.lastEvent,
  }));

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

  const networkLabel = networkState.lastError && networkState.status !== 'online'
    ? networkState.lastError
    : NETWORK_LABELS[networkState.status];
  const networkVariant = NETWORK_VARIANTS[networkState.status];

  const alertsVariant: 'ready' | 'warning' = diagnosticsState.count ? 'warning' : 'ready';
  const alertsLabel = diagnosticsState.count
    ? diagnosticsState.lastEvent
      ? truncate(
          diagnosticsState.count > 1
            ? `${diagnosticsState.count} alerts | ${diagnosticsState.lastEvent.message}`
            : diagnosticsState.lastEvent.message,
        )
      : `${diagnosticsState.count} alerts`
    : 'All clear';
  const alertsTitle = diagnosticsState.lastEvent
    ? `${diagnosticsState.lastEvent.message}${
        diagnosticsState.lastEvent.stack ? `\n${diagnosticsState.lastEvent.stack}` : ''
      }`
    : undefined;

  return (
    <footer className={styles.footer}>
      <div className={styles.section} title={alertsTitle}>
        <span className={styles.label}>Alerts</span>
        <StatusChip label={alertsLabel} status={alertsVariant} />
      </div>
      <div className={styles.section} title={networkState.lastError ?? undefined}>
        <span className={styles.label}>Network</span>
        <StatusChip label={truncate(networkLabel)} status={networkVariant} />
      </div>
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
