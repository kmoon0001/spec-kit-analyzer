import React from 'react';
import { StatusChip } from '../../../components/ui/StatusChip';
import styles from './AIHealthMonitor.module.css';

interface AIComponent {
  name: string;
  status: 'healthy' | 'degraded' | 'offline' | 'loading';
  details: string;
  lastCheck?: string;
  responseTime?: number;
}

interface AIHealthMonitorProps {
  components: AIComponent[];
  isLoading?: boolean;
  onRefresh?: () => void;
}

export const AIHealthMonitor: React.FC<AIHealthMonitorProps> = ({
  components,
  isLoading = false,
  onRefresh,
}) => {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'ready';
      case 'degraded':
        return 'warning';
      case 'loading':
        return 'warming';
      case 'offline':
      default:
        return 'offline';
    }
  };

  const getOverallHealth = () => {
    if (components.length === 0) return 'unknown';

    const healthyCount = components.filter(c => c.status === 'healthy').length;
    const degradedCount = components.filter(c => c.status === 'degraded').length;
    const offlineCount = components.filter(c => c.status === 'offline').length;

    if (offlineCount > 0) return 'critical';
    if (degradedCount > 0) return 'warning';
    if (healthyCount === components.length) return 'healthy';
    return 'unknown';
  };

  const overallHealth = getOverallHealth();

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>
          🤖 AI System Health
          <StatusChip
            label={overallHealth.toUpperCase()}
            status={getStatusVariant(overallHealth)}
          />
        </div>
        {onRefresh && (
          <button
            className={styles.refreshButton}
            onClick={onRefresh}
            disabled={isLoading}
          >
            {isLoading ? '⏳' : '🔄'} Refresh
          </button>
        )}
      </div>

      <div className={styles.componentsList}>
        {components.map((component) => (
          <div key={component.name} className={styles.componentItem}>
            <div className={styles.componentHeader}>
              <div className={styles.componentName}>{component.name}</div>
              <StatusChip
                label={component.status.toUpperCase()}
                status={getStatusVariant(component.status)}
              />
            </div>

            <div className={styles.componentDetails}>
              <div className={styles.detailsText}>{component.details}</div>

              <div className={styles.componentMeta}>
                {component.responseTime && (
                  <span className={styles.responseTime}>
                    ⚡ {component.responseTime}ms
                  </span>
                )}
                {component.lastCheck && (
                  <span className={styles.lastCheck}>
                    🕒 {new Date(component.lastCheck).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {components.length === 0 && !isLoading && (
        <div className={styles.noComponents}>
          No AI components detected. Check system configuration.
        </div>
      )}
    </div>
  );
};