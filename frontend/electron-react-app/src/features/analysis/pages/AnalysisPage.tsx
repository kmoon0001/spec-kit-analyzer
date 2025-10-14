import { useMemo, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';

import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { StatusChip } from '../../../components/ui/StatusChip';
import { fetchRubrics } from '../api';
import { useAnalysisController } from '../hooks/useAnalysisController';

import styles from './AnalysisPage.module.css';

const STRICTNESS_LEVELS = [
  {
    label: 'Clinical Essentials',
    description: 'Focus on core Medicare requirements for quick triage.',
  },
  {
    label: 'Regulatory Audit',
    description: 'Full compliance checklist including billing hygiene.',
  },
  {
    label: 'Director Review',
    description: 'Adds longitudinal outcomes, utilization, and PHI scrub accuracy.',
  },
];

const MODEL_STATUS = [
  { name: 'OpenMed NER', status: 'ready' as const },
  { name: 'S-PubMedBert', status: 'ready' as const },
  { name: 'FAISS + BM25', status: 'warming' as const },
  { name: 'Fact Checker', status: 'warming' as const },
  { name: 'Compliance LLM', status: 'ready' as const },
  { name: 'Chat Copilot', status: 'offline' as const },
];

export default function AnalysisPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const controller = useAnalysisController();
  const rubricsQuery = useQuery({ queryKey: ['rubrics'], queryFn: fetchRubrics });
  const rubrics = rubricsQuery.data ?? [];

  const disciplineOptions = useMemo(() => {
    const mapped = rubrics.map((rubric) => ({
      value: rubric.discipline,
      label: `${rubric.name} - ${rubric.discipline.toUpperCase()}`,
    }));
    if (!mapped.length) {
      return [
        { value: 'pt', label: 'Physical Therapy - Medicare Part B' },
        { value: 'ot', label: 'Occupational Therapy - Medicare Part A' },
        { value: 'slp', label: 'Speech-Language Pathology' },
      ];
    }
    return mapped;
  }, [rubrics]);

  const findings = controller.summary?.findings ?? [];
  const complianceScore = controller.summary?.complianceScore ?? null;
  const statusLabel = controller.status ? controller.status.replace(/_/g, ' ') : 'idle';
  const analysisError = controller.error instanceof Error ? controller.error : null;

  return (
    <div className={styles.wrapper}>
      <section className={styles.overviewStrip}>
        <div>
          <h2>Compliance Analysis Mission Control</h2>
          <p>
            Upload therapy documentation, select evaluation rubrics, and orchestrate AI-powered scoring that mirrors the PySide6 workflow.
          </p>
        </div>
        <div className={styles.overviewStats}>
          <Card variant="muted" title="Current Session" subtitle={controller.selectedFile?.name ?? 'Awaiting document'}>
            <div className={styles.metricRow}>
              <div>
                <span className={styles.metricLabel}>Compliance Score</span>
                <span className={styles.metricValue}>
                  {complianceScore !== null ? `${complianceScore.toFixed(1)}%` : controller.taskId ? '--%' : '-'}
                </span>
              </div>
              <div>
                <span className={styles.metricLabel}>Progress</span>
                <span className={styles.metricValue}>{controller.taskId ? `${controller.progress}%` : '0%'}</span>
              </div>
              <div>
                <span className={styles.metricLabel}>Status</span>
                <span className={styles.metricValue}>{statusLabel}</span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <section className={styles.columns}>
        <div className={styles.columnLeft}>
          <Card
            title="Document Intake"
            subtitle="Drag-and-drop or browse clinical narratives"
            actions={
              <Button variant="ghost" onClick={() => fileInputRef.current?.click()}>
                Browse Files
              </Button>
            }
          >
            <div
              className={`${styles.dropzone} ${controller.dropzone.isDragActive ? styles.dropzoneActive : ''}`}
              {...controller.dropzone.getRootProps()}
            >
              <input {...controller.dropzone.getInputProps()} ref={fileInputRef} />
              <span className={styles.dropzoneIcon}>[DOC]</span>
              {controller.selectedFile ? (
                <>
                  <p className={styles.fileName}>{controller.selectedFile.name}</p>
                  <p className={styles.dropzoneHint}>
                    {(controller.selectedFile.size / 1024 / 1024).toFixed(2)} MB - Local only, never uploaded externally
                  </p>
                </>
              ) : (
                <>
                  <p>Drop PDF, DOCX, or TXT files here</p>
                  <p className={styles.dropzoneHint}>HIPAA-safe: all processing remains local.</p>
                </>
              )}
            </div>
            {/* TODO: Connect batch queue and resume actions to mission-control orchestration. */}\n            <div className={styles.dropzoneActions}>
              <Button
                variant="primary"
                onClick={() => controller.startAnalysis()}
                disabled={!controller.selectedFile || controller.isStarting || controller.isPolling}
              >
                {controller.isStarting ? 'Starting...' : controller.taskId ? 'Re-run Analysis' : 'Start Full Analysis'}
              </Button>
              <Button variant="ghost" onClick={controller.reset} disabled={!controller.taskId && !controller.selectedFile}>
                Reset Session
              </Button>
            </div>
            {(controller.isStarting || controller.taskId) && (
              <div className={styles.progressWrapper}>
                <div className={styles.progressTrack}>
                  <div className={styles.progressBar} style={{ width: `${controller.progress}%` }} />
                </div>
                <span className={styles.progressText}>{controller.statusMessage}</span>
              </div>
            )}
            {analysisError && <p className={styles.errorText}>{analysisError.message}</p>}
          </Card>

          <Card title="Rubric Selection" subtitle="Load discipline-specific compliance rubrics">
            <label className={styles.fieldLabel} htmlFor="discipline">
              Clinical discipline
            </label>
            <select
              id="discipline"
              className={styles.select}
              value={controller.discipline}
              onChange={(event) => controller.setDiscipline(event.target.value)}
              disabled={rubricsQuery.isLoading}
            >
              {disciplineOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <div className={styles.rubricMeta}>
              <StatusChip label={`${rubrics.length || 3} rule sets`} status="ready" />
              <StatusChip label="Local cache" status="warming" />
            </div>
            <p className={styles.description}>
              Rubrics sync from <code>src/resources/</code> to ensure local parity with the PySide interface.
            </p>
          </Card>

          <Card title="Mission Controls" subtitle="Same quick actions as PySide6 mission control">
            <div className={styles.actionsGrid}>
              <Button
                variant="outline"
                onClick={() => controller.startAnalysis()}
                disabled={!controller.selectedFile || controller.isStarting}
              >
                Quick Risk Scan
              </Button>
              <Button variant="ghost">Open Batch Queue</Button>
              <Button variant="ghost">Launch Report Viewer</Button>
            </div>
          </Card>
        </div>

        <div className={styles.columnMiddle}>
          <Card title="Strictness & Guidelines" subtitle="Map to PySide strictness toggles">
            <div className={styles.strictnessList}>
              {STRICTNESS_LEVELS.map((level, index) => (
                <button
                  key={level.label}
                  type="button"
                  className={`${styles.strictnessItem} ${controller.strictness === index ? styles.strictnessActive : ''}`}
                  onClick={() => controller.setStrictness(index as 0 | 1 | 2)}
                >
                  <div className={styles.strictnessBullet}>*</div>
                  <div>
                    <p className={styles.strictnessTitle}>{level.label}</p>
                    <p className={styles.strictnessBody}>{level.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </Card>

          {/* TODO: Wire report configuration selections into backend preferences once API closes the loop. */}\n          <Card title="Report Configuration" subtitle="Matches ReportGenerator options">
            <ul className={styles.checkboxList}>
              {['Executive summary', 'Billing risk radar', 'Plan of care gaps', 'Narrative recommendations'].map(
                (section) => (
                  <li key={section}>
                    <label className={styles.checkboxItem}>
                      <input type="checkbox" defaultChecked />
                      <span>{section}</span>
                    </label>
                  </li>
                ),
              )}
            </ul>
            <div className={styles.reportFooter}>
              <StatusChip label="Med-branded PDF" status="ready" />
              <StatusChip label="HTML interactive" status="warming" />
            </div>
          </Card>

          <Card title="Licenses & Safeguards" subtitle="Mirrors PySide license checks">
            <p className={styles.description}>
              Local license validation and AI guardrails persist here; Electron bridges into the same backend services defined in <code>src/core</code>.
            </p>
            <Button variant="outline">Manage Feature Flags</Button>
          </Card>
        </div>

        <div className={styles.columnRight}>
          <Card title="Live Model Status" subtitle="Parity with StatusComponent">
            <div className={styles.modelStatusGrid}>
              {MODEL_STATUS.map((model) => (
                <div key={model.name} className={styles.modelStatusItem}>
                  <StatusChip label={model.name} status={model.status} />
                  <span className={styles.modelStatusHint}>
                    {model.status === 'ready' ? 'Ready' : model.status === 'offline' ? 'Awaiting warmup' : 'Preparing context'}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Findings Preview" subtitle="Structured output from AnalysisService">
            {!controller.taskId && <p className={styles.description}>Run an analysis to populate clinical findings.</p>}
            {controller.taskId && !controller.analysisComplete && !controller.analysisFailed && (
              <p className={styles.description}>Analysis running. Findings will stream in once complete.</p>
            )}
            {controller.analysisFailed && <p className={styles.errorText}>Analysis failed. Check logs for details.</p>}
            {controller.summary && controller.analysisComplete && (
              <ul className={styles.findingsList}>
                {findings.slice(0, 5).map((finding, index) => {
                  const key = String((finding as { id?: string })?.id ?? index);
                  const severityValue = (finding as { severity?: string | number })?.severity;
                  const severityLabel = severityValue !== undefined ? String(severityValue) : 'Info';
                  const statusVariant = severityLabel.toLowerCase() === 'high' ? 'warning' : 'warming';

                  return (
                    <li key={key}>
                      <div className={styles.findingHeader}>
                        <span className={styles.findingId}>{(finding as { id?: string })?.id ?? `F-${index + 1}`}</span>
                        <StatusChip label={severityLabel} status={statusVariant} />
                      </div>
                      <p>
                        {(finding as { description?: string; summary?: string })?.description ??
                          (finding as { description?: string; summary?: string })?.summary ??
                          'See detailed report.'}
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
            {controller.summary?.reportHtml && (
              <Button
                variant="outline"
                onClick={() => {
                  const blob = new Blob([controller.summary?.reportHtml ?? ''], { type: 'text/html' });
                  const url = URL.createObjectURL(blob);
                  window.open(url, '_blank');
                }}
              >
                Open Detailed Report
              </Button>
            )}
          </Card>

          <Card title="Compliance Copilot" subtitle="Chat assistant placeholder">
            <div className={styles.chatPlaceholder}>
              <p>
                The conversational assistant will connect to <code>src/api/routers/chat.py</code> via WebSocket streaming just like the PySide chat dialog.
              </p>
              <textarea className={styles.chatInput} placeholder="Ask about documentation gaps..." rows={3} />
              <div className={styles.chatActions}>
                <Button variant="primary">Send Prompt</Button>
                <Button variant="ghost">Insert Latest Finding</Button>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
