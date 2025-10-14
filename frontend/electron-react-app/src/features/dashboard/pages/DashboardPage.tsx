import { Card } from '../../../components/ui/Card';
import { StatusChip } from '../../../components/ui/StatusChip';

import styles from './DashboardPage.module.css';

const SCORE_CARDS = [
  { label: 'Average Compliance', value: '87%', delta: '+4.2%', tone: 'ready' as const },
  { label: 'High-Risk Findings', value: '12', delta: '-3 vs last week', tone: 'warning' as const },
  { label: 'Reports Generated', value: '48', delta: '+9%', tone: 'warming' as const },
];

const DISCIPLINE_BREAKDOWN = [
  { name: 'Physical Therapy', score: 90 },
  { name: 'Occupational Therapy', score: 83 },
  { name: 'Speech', score: 78 },
];

const WORKQUEUE = [
  { id: 'DOC-4581', owner: 'Therapist Kim', status: 'Quality Review' },
  { id: 'DOC-4579', owner: 'Therapist Singh', status: 'Pending Findings' },
  { id: 'DOC-4574', owner: 'Therapist Ortiz', status: 'Ready to Publish' },
];

export default function DashboardPage() {
  return (
    <div className={styles.dashboard}>
      <header>
        <h2>Compliance Intelligence Dashboard</h2>
        <p>
          Mirrors the PySide6 dashboard tab with mission-critical metrics, now optimized for React/Electron rendering.
        </p>
      </header>

      <section className={styles.metricsRow}>
        {SCORE_CARDS.map((card) => (
          <Card key={card.label}>
            <span className={styles.metricLabel}>{card.label}</span>
            <span className={styles.metricValue}>{card.value}</span>
            <StatusChip label={card.delta} status={card.tone} />
          </Card>
        ))}
      </section>

      <section className={styles.gridTwo}>
        <Card title="Discipline Compliance" subtitle="Ported from DashboardWidget charts">
          <ul className={styles.listPlain}>
            {DISCIPLINE_BREAKDOWN.map((row) => (
              <li key={row.name}>
                <span>{row.name}</span>
                <div className={styles.progressBar}>
                  <div style={{ width: `${row.score}%` }} />
                </div>
                <span className={styles.progressValue}>{row.score}%</span>
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Mission Control Queue" subtitle="Active compliance reviews">
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Document</th>
                <th>Owner</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {WORKQUEUE.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  <td>{row.owner}</td>
                  <td>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>

      <section className={styles.gridTwo}>
        <Card title="Compliance Timeline" subtitle="Future home for time-series charts">
          <div className={styles.placeholder}>Interactive chart components will render here using Recharts once data wiring is complete.</div>
        </Card>
        <Card title="Licensing & Feature Flags" subtitle="Synced from PySide admin widgets">
          <ul className={styles.flagList}>
            <li>
              <StatusChip label="Local models" status="ready" />
              Running optimized quantized builds
            </li>
            <li>
              <StatusChip label="Advanced QA" status="warming" />
              Cross-check mode scheduled nightly
            </li>
            <li>
              <StatusChip label="EHR Connector" status="offline" />
              Disabled until credentials configured
            </li>
          </ul>
        </Card>
      </section>
    </div>
  );
}
