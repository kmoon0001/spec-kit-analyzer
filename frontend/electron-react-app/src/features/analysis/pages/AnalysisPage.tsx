import { useRef, useState } from 'react';

import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { StatusChip } from '../../../components/ui/StatusChip';
import { useAnalysisController } from '../hooks/useAnalysisController';
import { useDesktopTelemetry } from '../../system/hooks/useDesktopTelemetry';
import { ChatAssistant } from '../components/ChatAssistant';
import { HelpSystem } from '../components/HelpSystem';
import { ReportDialog } from '../components/ReportDialog';
import { LibrarySelectionDialog } from '../components/LibrarySelectionDialog';
import { CitationManager } from '../components/CitationManager';

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
  { name: 'Meditron-7B Clinical AI', status: 'ready' as const },
  { name: 'Chat Copilot', status: 'offline' as const },
];

export default function AnalysisPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const controller = useAnalysisController();
  const telemetry = useDesktopTelemetry();
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [showLibraryDialog, setShowLibraryDialog] = useState(false);
  const [showCitationManager, setShowCitationManager] = useState(false);

  const findings = controller.summary?.findings ?? [];
  const complianceScore = controller.summary?.complianceScore ?? null;
  const analysisError = controller.error instanceof Error ? controller.error : null;
  const progressPercent = Math.max(0, Math.min(100, Math.round(controller.progress ?? 0)));
  const telemetryCpu = telemetry.metrics.cpuPercent !== null ? `${telemetry.metrics.cpuPercent.toFixed(1)}%` : '--';
  const telemetryMemory = telemetry.metrics.memoryMb !== null ? `${Math.round(telemetry.metrics.memoryMb)} MB` : '--';
  const telemetryLoop = telemetry.metrics.eventLoopP99 !== null ? `${telemetry.metrics.eventLoopP99.toFixed(1)} ms` : '--';
  const telemetryActiveSummary = telemetry.snapshot
    ? `${telemetry.metrics.activeCount}/${typeof telemetry.snapshot.concurrency === 'number' ? telemetry.snapshot.concurrency : '--'}`
    : `${telemetry.metrics.activeCount}/--`;
  const telemetryQueueSummary = telemetry.metrics.queueSize;
  const telemetryUpdatedLabel = telemetry.lastUpdatedAt
    ? new Date(telemetry.lastUpdatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : 'Awaiting data';

  const statusLabel = controller.status ? controller.status.replace(/_/g, ' ') : controller.isPolling ? 'running' : 'idle';

  return (
    <div className={styles.wrapper}>
      <section className={styles.overviewStrip}>
        <div>
          <h2>Compliance Analysis Mission Control</h2>
          <p>
            Upload therapy documentation, select evaluation targets, and orchestrate AI-powered scoring that mirrors the PySide workflows while staying responsive on desktop.
          </p>
          <div className={styles.runtimePillRow}>
            <StatusChip label={controller.isDesktop ? 'Desktop Runtime' : 'Browser Runtime'} status={controller.isDesktop ? 'ready' : 'warming'} />
            <StatusChip label={controller.isPolling ? 'Task Active' : 'Idle'} status={controller.isPolling ? 'ready' : 'offline'} />
          </div>
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
                <span className={styles.metricValue}>{controller.taskId || controller.isPolling ? `${progressPercent}%` : '0%'}</span>
              </div>
              <div>
                <span className={styles.metricLabel}>Status</span>
                <span className={styles.metricValue}>{statusLabel}</span>
              </div>
            </div>
          </Card>
          {controller.isDesktop && telemetry.isSupported && (
            <Card variant="muted" title="Runtime Telemetry" subtitle="Main & worker health">
              <div className={styles.telemetryGrid}>
                <div>
                  <span className={styles.metricLabel}>CPU</span>
                  <span className={styles.metricValue}>{telemetryCpu}</span>
                </div>
                <div>
                  <span className={styles.metricLabel}>Memory</span>
                  <span className={styles.metricValue}>{telemetryMemory}</span>
                </div>
                <div>
                  <span className={styles.metricLabel}>Loop p99</span>
                  <span className={styles.metricValue}>{telemetryLoop}</span>
                </div>
              </div>
              <div className={styles.telemetryMetaRow}>
                <span>Active {telemetryActiveSummary}</span>
                <span>Queue {telemetryQueueSummary}</span>
                <span>{telemetryUpdatedLabel}</span>
              </div>
              {telemetry.snapshot?.workers.length ? (
                <ul className={styles.telemetryWorkerList}>
                  {telemetry.snapshot.workers.slice(0, 3).map((worker) => (
                    <li key={worker.jobId}>
                      <span>{worker.type}</span>
                      <span>{Math.max(0, Math.round(worker.runtimeMs / 1000))}s</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className={styles.telemetryIdleText}>Workers idle</p>
              )}
            </Card>
          )}
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
              <span className={styles.dropzoneIcon} aria-hidden>
                [DOC]
              </span>
              {controller.selectedFile ? (
                <>
                  <p className={styles.fileName}>{controller.selectedFile.name}</p>
                  <p className={styles.dropzoneHint}>
                    {(controller.selectedFile.size / 1024 / 1024).toFixed(2)} MB - Stored locally until you start analysis
                  </p>
                </>
              ) : (
                <>
                  <p>Drop PDF, DOCX, or TXT files here</p>
                  <p className={styles.dropzoneHint}>HIPAA-safe: heavy processing offloads to secure workers.</p>
                </>
              )}
            </div>

            <div className={styles.progressWrapper}>
              <div className={styles.progressMeta}>
                <span>{statusLabel}</span>
                <span>{`${progressPercent}%`}</span>
              </div>
              <div className={styles.progressTrack} role="progressbar" aria-valuenow={progressPercent} aria-valuemin={0} aria-valuemax={100}>
                <div className={styles.progressBar} style={{ width: `${progressPercent}%` }} />
              </div>
              <span className={styles.progressStatus}>{controller.statusMessage}</span>
            </div>

            {analysisError && <div className={styles.errorBanner}>{analysisError.message}</div>}

            <div className={styles.dropzoneActions}>
              <Button
                variant="primary"
                onClick={controller.startAnalysis}
                disabled={!controller.selectedFile || controller.isStarting || controller.isPolling}
              >
                {controller.isStarting ? 'Starting...' : controller.isPolling ? 'Running...' : 'Start Analysis'}
              </Button>
              <Button variant="outline" onClick={controller.cancelAnalysis} disabled={!controller.isPolling || !controller.isDesktop}>
                Cancel
              </Button>
              <Button variant="ghost" onClick={controller.reset} disabled={controller.isPolling && controller.isDesktop}>
                Reset
              </Button>
            </div>
            <p className={styles.intakeHint}>
              Background workers stream progress without blocking the UI. Cancel gracefully when inference takes too long.
            </p>
          </Card>

          <Card title="Discipline & Rubrics" subtitle="Auto-detected based on document content">
            <div className={styles.selectRow}>
              <label className={styles.label}>Therapy Discipline:</label>
              <select
                className={styles.selectControl}
                value={controller.discipline}
                onChange={(event) => controller.setDiscipline(event.target.value)}
              >
                <option value="all">All Disciplines</option>
                <option value="pt">Physical Therapy (PT)</option>
                <option value="ot">Occupational Therapy (OT)</option>
                <option value="slp">Speech-Language Pathology (SLP)</option>
              </select>
              {controller.autoDetectedDiscipline && (
                <span className={styles.autoDetected}>
                  🤖 Auto-detected: {controller.autoDetectedDiscipline.toUpperCase()}
                </span>
              )}
            </div>

            <div className={styles.selectRow}>
              <label className={styles.label}>Compliance Rubric:</label>
              <select
                className={styles.selectControl}
                value={controller.selectedRubric || 'default'}
                onChange={(event) => controller.setSelectedRubric(event.target.value)}
              >
                <option value="default">📋 Medicare Benefits Policy Manual - Chapter 15</option>
                <option value="medicare_part_b">📋 Medicare Part B Outpatient Therapy Guidelines</option>
                <option value="cms_1500">📋 CMS-1500 Documentation Requirements</option>
                <option value="therapy_cap">📋 Medicare Therapy Cap & Exception Guidelines</option>
                <option value="skilled_therapy">📋 Skilled Therapy Documentation Standards</option>
                <option value="apta_pt">🏃 Physical Therapy - APTA Guidelines</option>
                <option value="aota_ot">🖐️ Occupational Therapy - AOTA Standards</option>
                <option value="asha_slp">🗣️ Speech-Language Pathology - ASHA Guidelines</option>
              </select>
              {controller.autoDetectedRubric && (
                <span className={styles.autoDetected}>
                  🎯 Auto-detected: {controller.autoDetectedRubric}
                </span>
              )}
            </div>

            <div className={styles.rubricDescription}>
              <p className={styles.description}>
                {controller.selectedRubric === 'default' && 'Comprehensive Medicare coverage policies for medical services including therapy requirements.'}
                {controller.selectedRubric === 'medicare_part_b' && 'Specific guidelines for outpatient therapy services under Medicare Part B.'}
                {controller.selectedRubric === 'cms_1500' && 'Documentation standards required for CMS-1500 claim forms.'}
                {controller.selectedRubric === 'therapy_cap' && 'Guidelines for therapy cap exceptions and documentation requirements.'}
                {controller.selectedRubric === 'skilled_therapy' && 'Standards for documenting skilled therapy services and medical necessity.'}
                {controller.selectedRubric === 'apta_pt' && 'American Physical Therapy Association clinical practice guidelines.'}
                {controller.selectedRubric === 'aota_ot' && 'American Occupational Therapy Association practice standards.'}
                {controller.selectedRubric === 'asha_slp' && 'American Speech-Language-Hearing Association clinical guidelines.'}
              </p>
              {controller.rubricSuggestions && controller.rubricSuggestions.length > 1 && (
                <div className={styles.rubricSuggestions}>
                  <p className={styles.suggestionLabel}>Other suggested rubrics:</p>
                  <ul className={styles.suggestionList}>
                    {controller.rubricSuggestions.slice(1, 4).map((suggestion, index) => (
                      <li key={index} className={styles.suggestionItem}>
                        <button
                          type="button"
                          className={styles.suggestionButton}
                          onClick={() => controller.setSelectedRubric(suggestion.rubric_id)}
                        >
                          {suggestion.rubric_id.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                          <span className={styles.confidence}>
                            ({Math.round(suggestion.confidence * 100)}% match)
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>

          <Card title="Strictness" subtitle="Mirrors PySide toggle set">
            <div className={styles.strictnessList}>
              {STRICTNESS_LEVELS.map((level, index) => {
                const isActive = controller.strictness === index;
                return (
                  <button
                    type="button"
                    key={level.label}
                    className={`${styles.strictnessCard} ${isActive ? styles.strictnessActive : ''}`}
                    onClick={() => controller.setStrictness(index as 0 | 1 | 2)}
                  >
                    <span className={styles.strictnessBullet}>{'>'}</span>
                    <div>
                      <p className={styles.strictnessTitle}>{level.label}</p>
                      <p className={styles.strictnessBody}>{level.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>

          <Card title="Report Configuration" subtitle="Matches ReportGenerator options">
            <ul className={styles.checkboxList}>
              {['Executive summary', 'Billing risk radar', 'Plan of care gaps', 'Narrative recommendations'].map((section) => (
                <li key={section}>
                  <label className={styles.checkboxItem}>
                    <input type="checkbox" defaultChecked />
                    <span>{section}</span>
                  </label>
                </li>
              ))}
            </ul>
            <div className={styles.reportFooter}>
              <StatusChip label="Med-branded PDF" status="ready" />
              <StatusChip label="HTML interactive" status="warming" />
            </div>
          </Card>

          <Card title="Licenses & Safeguards" subtitle="Parity with PySide guardrails">
            <p className={styles.description}>
              Electron reuses backend license checks and audit logging. Background workers surface crash signals so desktop ops stay stable.
            </p>
            <div className={styles.safeguardActions}>
              <Button variant="outline" onClick={() => setShowLibraryDialog(true)}>
                📚 Manage Rubric Library
              </Button>
              <Button variant="outline" onClick={() => setShowCitationManager(true)}>
                📖 Citation Manager
              </Button>
            </div>
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
              <p className={styles.description}>Analysis running. Findings stream in once complete.</p>
            )}
            {controller.analysisFailed && (
              <p className={styles.errorText}>Analysis failed. Check logs or retry when resources recover.</p>
            )}
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
              <div className={styles.reportActions}>
                <Button
                  variant="outline"
                  onClick={() => setShowReportDialog(true)}
                >
                  📊 Open Detailed Report
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    const blob = new Blob([controller.summary?.reportHtml ?? ''], { type: 'text/html' });
                    const url = URL.createObjectURL(blob);
                    window.open(url, '_blank');
                  }}
                >
                  🔗 View in Browser
                </Button>
              </div>
            )}
          </Card>

          <ChatAssistant
            initialContext={controller.summary ?
              `I just analyzed a ${controller.discipline.toUpperCase()} document with a compliance score of ${controller.summary.complianceScore?.toFixed(1)}%. Can you help me understand the findings?`
              : undefined
            }
          />
        </div>
      </section>

      {/* Help System */}
      <section className={styles.helpSection}>
        <HelpSystem />
      </section>

      {/* Report Dialog */}
      {showReportDialog && controller.summary && (
        <div className={styles.dialogOverlay}>
          <ReportDialog
            reportHtml={controller.summary.reportHtml || ''}
            reportData={{
              complianceScore: controller.summary.complianceScore || 0,
              findings: controller.summary.findings || [],
              documentName: controller.selectedFile?.name || 'Unknown Document',
              analysisDate: new Date().toISOString(),
              discipline: controller.discipline,
              rubric: controller.selectedRubric || 'default'
            }}
            onClose={() => setShowReportDialog(false)}
          />
        </div>
      )}

      {/* Library Selection Dialog */}
      {showLibraryDialog && (
        <LibrarySelectionDialog
          onSelect={(rubric) => {
            controller.setSelectedRubric(rubric.id);
            setShowLibraryDialog(false);
          }}
          onClose={() => setShowLibraryDialog(false)}
        />
      )}

      {/* Citation Manager */}
      {showCitationManager && (
        <div className={styles.dialogOverlay}>
          <CitationManager
            onSelect={(citation) => {
              console.log('Selected citation:', citation);
            }}
            onInsert={(citation) => {
              console.log('Inserting citation:', citation);
            }}
            onClose={() => setShowCitationManager(false)}
          />
        </div>
      )}
    </div>
  );
}
