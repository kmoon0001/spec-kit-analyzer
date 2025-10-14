import { ChangeEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { StatusChip } from '../../../components/ui/StatusChip';
import { useAppStore } from '../../../store/useAppStore';
import { fetchPreferences, updatePreferences, PreferencesForm } from '../api';

import styles from './SettingsPage.module.css';

const TOGGLES = [
  { key: 'enableBetaWidgets', label: 'Enable beta mission-control widgets' },
  { key: 'autoStartBackend', label: 'Auto-start FastAPI backend with Electron shell' },
  { key: 'streamAnalysisLogs', label: 'Stream analysis logs to dashboard' },
] as const;

const PERFORMANCE_FLAGS = [
  { label: 'GPU acceleration', status: 'ready' as const, hint: 'Auto-detected NVidia runtime' },
  { label: 'Model quantization', status: 'ready' as const, hint: 'Running Q4_K_M profile' },
  { label: 'Deep fact checker', status: 'warming' as const, hint: 'Disabled for speed mode' },
];

const strictnessLabels: Record<PreferencesForm['defaultStrictness'], string> = {
  lenient: 'Clinical Essentials',
  standard: 'Regulatory Audit',
  strict: 'Director Review',
};

const exportFormatLabels: Record<PreferencesForm['autoExportFormat'], string> = {
  pdf: 'Medical PDF',
  pdf_html: 'Medical PDF + HTML',
};

export default function SettingsPage() {
  const token = useAppStore((state) => state.auth.token);
  const [formState, setFormState] = useState<PreferencesForm | null>(null);

  const preferencesQuery = useQuery({
    queryKey: ['user-preferences'],
    queryFn: fetchPreferences,
    enabled: Boolean(token),
  });

  const saveMutation = useMutation({
    mutationFn: updatePreferences,
    onSuccess: (data) => {
      setFormState(data);
    },
  });

  useEffect(() => {
    if (preferencesQuery.data) {
      setFormState(preferencesQuery.data);
    }
  }, [preferencesQuery.data]);

  const isSaving = saveMutation.isPending;

  const handleSelectChange = useCallback(<K extends keyof PreferencesForm>(key: K) => (event: ChangeEvent<HTMLSelectElement>) => {
    setFormState((prev) => (prev ? { ...prev, [key]: event.target.value as PreferencesForm[K] } : prev));
  }, []);

  const handleToggleChange = useCallback(<K extends keyof PreferencesForm>(key: K) => (event: ChangeEvent<HTMLInputElement>) => {
    setFormState((prev) => (prev ? { ...prev, [key]: event.target.checked as PreferencesForm[K] } : prev));
  }, []);

  const handleSave = useCallback(() => {
    if (!formState || isSaving) {
      return;
    }
    saveMutation.mutate(formState);
  }, [formState, isSaving, saveMutation]);

  const saveLabel = useMemo(() => {
    if (isSaving) {
      return 'Saving...';
    }
    if (saveMutation.isSuccess) {
      return 'Preferences saved';
    }
    return 'Save Preferences';
  }, [isSaving, saveMutation.isSuccess]);

  return (
    <div className={styles.settings}>
      <header>
        <h2>Application Settings</h2>
        <p>
          Maps to the PySide settings tab—user preferences, report customization, and advanced administrator tooling.
        </p>
      </header>

      <section className={styles.gridTwo}>
        <Card title="User Preferences" subtitle="Appearance, notifications, and session defaults">
          {preferencesQuery.isLoading && <p className={styles.helperText}>Loading preferences...</p>}
          {preferencesQuery.isError && (
            <p className={styles.errorText}>Unable to load preferences. Ensure the API is available.</p>
          )}
          {formState && (
            <>
              <div className={styles.preferenceGroup}>
                <label>
                  <span>Default theme</span>
                  <select value={formState.themeMode} onChange={handleSelectChange('themeMode')}>
                    <option value="system">Adaptive (System)</option>
                    <option value="light">Always Light</option>
                    <option value="dark">Always Dark</option>
                  </select>
                </label>
                <label>
                  <span>Startup screen</span>
                  <select value={formState.startupScreen} onChange={handleSelectChange('startupScreen')}>
                    <option value="analysis">Analysis workspace</option>
                    <option value="dashboard">Dashboard</option>
                    <option value="mission_control">Mission Control</option>
                  </select>
                </label>
              </div>
              <div className={styles.toggleList}>
                {TOGGLES.map((toggle) => (
                  <label key={toggle.label} className={styles.toggleItem}>
                    <input
                      type="checkbox"
                      checked={formState[toggle.key] as boolean}
                      onChange={handleToggleChange(toggle.key)}
                    />
                    <span>{toggle.label}</span>
                  </label>
                ))}
              </div>
            </>
          )}
          <Button variant="outline" disabled={!formState || isSaving} onClick={handleSave}>
            {saveLabel}
          </Button>
          {saveMutation.isError && <p className={styles.errorText}>Failed to save preferences. Try again.</p>}
        </Card>

        <Card title="Report & Compliance Settings" subtitle="Backed by ReportGenerator and guideline services">
          {formState ? (
            <>
              <div className={styles.settingItem}>
                <span>Default rubric strictness</span>
                <select value={formState.defaultStrictness} onChange={handleSelectChange('defaultStrictness')}>
                  <option value="lenient">{strictnessLabels.lenient}</option>
                  <option value="standard">{strictnessLabels.standard}</option>
                  <option value="strict">{strictnessLabels.strict}</option>
                </select>
              </div>
              <div className={styles.settingItem}>
                <span>Auto-export format</span>
                <select value={formState.autoExportFormat} onChange={handleSelectChange('autoExportFormat')}>
                  <option value="pdf">{exportFormatLabels.pdf}</option>
                  <option value="pdf_html">{exportFormatLabels.pdf_html}</option>
                </select>
              </div>
            </>
          ) : (
            <p className={styles.helperText}>Preferences will appear once loaded.</p>
          )}
          <p className={styles.helperText}>
            These options map directly to <code>src/core/report_generator.py</code> and <code>src/gui/components/settings_tab_builder.py</code> behaviours.
          </p>
        </Card>
      </section>

      <section className={styles.gridTwo}>
        <Card title="Performance" subtitle="Parallels the PySide settings performance tab">
          <ul className={styles.flagList}>
            {PERFORMANCE_FLAGS.map((flag) => (
              <li key={flag.label}>
                <StatusChip label={flag.label} status={flag.status} />
                <span>{flag.hint}</span>
              </li>
            ))}
          </ul>
          {/* TODO: Wire profiler launcher once the diagnostics window ships to Electron. */}
          <Button variant="ghost">Open Profiler</Button>
        </Card>
        <Card title="Administrative Controls" subtitle="SettingsEditorWidget parity">
          <p className={styles.helperText}>
            The Electron frontend will call the same configuration endpoints exposed by <code>src/api/routers/admin.py</code> for persistent updates.
          </p>
          <Button variant="primary">Open Advanced Editor</Button>
        </Card>
      </section>
    </div>
  );
}

