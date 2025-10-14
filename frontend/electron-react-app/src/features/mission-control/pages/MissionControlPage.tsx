import { useMemo } from 'react';

import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { StatusChip } from '../../../components/ui/StatusChip';
import { useTaskMonitor } from '../../analysis/hooks/useTaskMonitor';
import { useLogStream } from '../hooks/useLogStream';
import { useAppStore } from '../../../store/useAppStore';

import styles from './MissionControlPage.module.css';

const TEMPLATE_NAMES = [
  'Medicare Part B Orthopedic Progress Note',
  'Outpatient Neuro Follow-up',
  'Pediatric OT Initial Evaluation',
];

export default function MissionControlPage() {
  const token = useAppStore((state) => state.auth.token);
  const taskQuery = useTaskMonitor({ enabled: Boolean(token) });
  const logStream = useLogStream();

  const tasks = useMemo(() => {
    const entries = taskQuery.data ? Object.entries(taskQuery.data) : [];
    if (!entries.length) {
      return [];
    }
    return entries.map(([id, task]) => ({
      id,
      label: `${task.filename ?? 'Document'} · ${task.status_message ?? task.status ?? 'pending'}`,
      status: task.status ?? 'pending',
    }));
  }, [taskQuery.data]);

  return (
    <div className={styles.mission}>
      <header>
        <h2>Mission Control Console</h2>
        <p>
          Provides the same orchestration surface as the PySide mission control tab—quick actions, task telemetry, and live logs.
        </p>
      </header>

      <section className={styles.grid}>
        <Card title="Launch Actions" subtitle="Mirrors mission_control_widget triggers">
          <div className={styles.actionsList}>
            <Button variant="primary">Resume Last Analysis</Button>
            <Button variant="outline">Seed Demo Dataset</Button>
            <Button variant="ghost">Open Advanced Scheduler</Button>
            <Button variant="ghost">Show API Diagnostics</Button>
          </div>
          <div className={styles.templateList}>
            <p>Recent templates</p>
            <ul>
              {TEMPLATE_NAMES.map((template) => (
                <li key={template}>{template}</li>
              ))}
            </ul>
          </div>
        </Card>

        <Card title="Active Tasks" subtitle="Hybrid of local + API tasks, matching ViewModel merging">
          {!tasks.length && <p className={styles.helperText}>No tasks running. Start an analysis to populate this list.</p>}
          <ul className={styles.taskList}>
            {tasks.map((task) => (
              <li key={task.id}>
                <div>
                  <span className={styles.taskId}>{task.id}</span>
                  <p>{task.label}</p>
                </div>
                <StatusChip
                  label={task.status === 'completed' ? 'Completed' : task.status ?? 'Pending'}
                  status={task.status === 'completed' ? 'ready' : task.status === 'failed' ? 'warning' : 'warming'}
                />
              </li>
            ))}
          </ul>
          <Button variant="ghost" onClick={() => taskQuery.refetch()}>
            Refresh Tasks
          </Button>
        </Card>

        <Card title="Live Log Stream" subtitle="Streaming via websocket router in FastAPI">
          <div className={styles.logPane}>
            {logStream.connectionError && <p className={styles.helperText}>{logStream.connectionError}</p>}
            {!logStream.connectionError && (
              <pre>{logStream.messages.slice(-20).join('\n')}</pre>
            )}
          </div>
          <div className={styles.logActions}>
            <Button variant="outline">Export Logs</Button>
            <Button variant="ghost">Clear Console</Button>
          </div>
        </Card>
      </section>
    </div>
  );
}
