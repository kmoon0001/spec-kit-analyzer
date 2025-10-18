import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';

import { analyzeDocument, fetchAnalysisStatus, AnalysisStatus } from '../api';
import { getConfig } from '../../../lib/config';
import { useAppStore } from '../../../store/useAppStore';

const STRICTNESS_OPTIONS = ['lenient', 'standard', 'strict'] as const;
type StrictnessLevel = 0 | 1 | 2;

type DesktopAnalysisState = {
  jobId: string | null;
  status: 'idle' | 'starting' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  statusMessage: string;
  progress: number;
  result: AnalysisStatus | null;
  error: Error | null;
  isPolling: boolean;
  meta?: Record<string, unknown> | null;
};

const INITIAL_DESKTOP_STATE: DesktopAnalysisState = {
  jobId: null,
  status: 'idle',
  statusMessage: 'Waiting to start',
  progress: 0,
  result: null,
  error: null,
  isPolling: false,
  meta: null,
};

const isDesktopRuntime = () => typeof window !== 'undefined' && Boolean(window.desktopApi?.tasks);

const toError = (error: unknown): Error => {
  if (error instanceof Error) {
    return error;
  }
  const message = typeof error === 'string' ? error : 'Unexpected error occurred';
  return new Error(message);
};

const clampProgress = (value: number | undefined, fallback: number) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return fallback;
  }
  if (value < 0) {
    return 0;
  }
  if (value > 100) {
    return 100;
  }
  return Math.round(value);
};

export const useAnalysisController = () => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [discipline, setDiscipline] = useState('pt');
  const [analysisMode] = useState('rubric');
  const [strictness, setStrictnessState] = useState<StrictnessLevel>(1);
  const [taskId, setTaskId] = useState<string | null>(null);
  const strictnessLevel = STRICTNESS_OPTIONS[strictness];

  const config = getConfig();
  const token = useAppStore((state) => state.auth.token);
  const desktopEnabled = isDesktopRuntime();

  const [desktopState, setDesktopState] = useState<DesktopAnalysisState>(INITIAL_DESKTOP_STATE);
  const activeDesktopJobIdRef = useRef<string | null>(null);

  const setStrictness = useCallback((value: StrictnessLevel) => {
    setStrictnessState(value);
  }, []);

  const startMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) {
        throw new Error('Select a document before starting analysis.');
      }
      return analyzeDocument({
        file: selectedFile,
        discipline,
        analysisMode,
        strictness: strictnessLevel,
      });
    },
    onSuccess: (response) => {
      setTaskId(response.task_id);
    },
  });

  const statusQuery = useQuery<AnalysisStatus>({
    queryKey: ['analysis-status', taskId],
    queryFn: () => fetchAnalysisStatus(taskId as string),
    enabled: Boolean(taskId) && !desktopEnabled,
    refetchInterval: (query) => {
      if (desktopEnabled) {
        return false;
      }
      const data = query.state.data;
      if (!data || data.status !== 'completed') {
        return 1500;
      }
      return false;
    },
  });

  useEffect(() => {
    if (!desktopEnabled || !window.desktopApi?.tasks) {
      return;
    }

    const tasksApi = window.desktopApi.tasks;

    const handleQueued = (event: DesktopTaskEventPayload) => {
      if (event.jobId !== activeDesktopJobIdRef.current) {
        return;
      }
      const job = event.job;
      if (!job) {
        return;
      }
      setDesktopState((prev) => ({
        ...prev,
        status: 'queued',
        statusMessage: job.statusMessage ?? 'Queued for processing',
        progress: clampProgress(job.progress, prev.progress),
        isPolling: true,
        meta: job.meta ?? prev.meta ?? null,
      }));
    };

    const handleStarted = (event: DesktopTaskEventPayload) => {
      if (event.jobId !== activeDesktopJobIdRef.current) {
        return;
      }
      const job = event.job;
      if (!job) {
        return;
      }
      setDesktopState((prev) => ({
        ...prev,
        status: 'running',
        statusMessage: job.statusMessage ?? 'Running analysis',
        progress: clampProgress(job.progress, prev.progress),
        isPolling: true,
        meta: job.meta ?? prev.meta ?? null,
      }));
    };

    const handleProgress = (event: DesktopTaskEventPayload) => {
      if (event.jobId !== activeDesktopJobIdRef.current) {
        return;
      }
      const job = event.job;
      if (!job) {
        return;
      }
      setDesktopState((prev) => ({
        ...prev,
        status: 'running',
        statusMessage: job.statusMessage ?? prev.statusMessage,
        progress: clampProgress(job.progress, prev.progress),
        isPolling: true,
        meta: job.meta ?? prev.meta ?? null,
      }));

      const taskMeta = job.meta as { taskId?: string } | undefined;
      if (taskMeta?.taskId) {
        setTaskId((current) => current ?? taskMeta.taskId ?? null);
      }
    };

    const handleCompleted = (event: DesktopTaskEventPayload) => {
      if (event.jobId !== activeDesktopJobIdRef.current) {
        return;
      }
      const job = event.job;
      if (!job) {
        return;
      }
      activeDesktopJobIdRef.current = null;
      const result = job.result as AnalysisStatus | null;
      const taskMeta = job.meta as { taskId?: string } | undefined;
      if (taskMeta?.taskId) {
        setTaskId(taskMeta.taskId);
      }
      setDesktopState((prev) => ({
        ...prev,
        status: 'completed',
        statusMessage: job.statusMessage ?? 'Analysis completed',
        progress: 100,
        result: result ?? prev.result,
        isPolling: false,
        meta: job.meta ?? prev.meta ?? null,
      }));
    };

    const handleFailed = (event: DesktopTaskEventPayload) => {
      if (event.jobId !== activeDesktopJobIdRef.current) {
        return;
      }
      const job = event.job;
      if (!job) {
        return;
      }
      activeDesktopJobIdRef.current = null;
      const errorMessage = job.error?.message ?? job.statusMessage ?? 'Analysis failed';
      const errorObject = toError(errorMessage);
      setDesktopState((prev) => ({
        ...prev,
        status: 'failed',
        statusMessage: errorMessage,
        progress: clampProgress(job.progress, prev.progress),
        error: errorObject,
        isPolling: false,
        meta: job.meta ?? prev.meta ?? null,
      }));
    };

    const handleCancelled = (event: DesktopTaskEventPayload) => {
      if (event.jobId !== activeDesktopJobIdRef.current) {
        return;
      }
      const job = event.job;
      if (!job) {
        return;
      }
      activeDesktopJobIdRef.current = null;
      setDesktopState((prev) => ({
        ...prev,
        status: 'cancelled',
        statusMessage: job.statusMessage ?? 'Analysis cancelled',
        progress: clampProgress(job.progress, prev.progress),
        isPolling: false,
        meta: job.meta ?? prev.meta ?? null,
      }));
    };

    const unsubscribes = [
      tasksApi.on('queued', handleQueued),
      tasksApi.on('started', handleStarted),
      tasksApi.on('progress', handleProgress),
      tasksApi.on('completed', handleCompleted),
      tasksApi.on('failed', handleFailed),
      tasksApi.on('cancelled', handleCancelled),
    ];

    return () => {
      unsubscribes.forEach((unsubscribe) => {
        try {
          unsubscribe();
        } catch (error) {
          console.warn('Failed to unsubscribe from task event', error);
        }
      });
    };
  }, [desktopEnabled]);

  const startDesktopAnalysis = useCallback(async () => {
    if (!desktopEnabled || !window.desktopApi?.tasks) {
      throw new Error('Desktop analysis is not available in this runtime.');
    }
    if (!selectedFile) {
      throw new Error('Select a document before starting analysis.');
    }

    setDesktopState({
      ...INITIAL_DESKTOP_STATE,
      status: 'starting',
      statusMessage: 'Preparing document',
      progress: 2,
      isPolling: true,
    });
    setTaskId(null);
    activeDesktopJobIdRef.current = null;

    try {
      const fileBuffer = await selectedFile.arrayBuffer();
      const payload = {
        fileName: selectedFile.name,
        fileBuffer,
        size: selectedFile.size,
        lastModified: selectedFile.lastModified,
        discipline,
        analysisMode,
        strictness: strictnessLevel,
      };

      const response = await window.desktopApi.tasks.startAnalysis(payload, {
        metadata: {
          token,
          apiBaseUrl: config.apiBaseUrl,
          pollIntervalMs: 1500,
          timeoutMs: 15 * 60 * 1000,
        },
      });

      activeDesktopJobIdRef.current = response.jobId;
      setDesktopState((prev) => ({
        ...prev,
        jobId: response.jobId,
        status: 'queued',
        statusMessage: 'Queued for processing',
        progress: 5,
        isPolling: true,
      }));
    } catch (error) {
      const err = toError(error);
      activeDesktopJobIdRef.current = null;
      setDesktopState({
        ...INITIAL_DESKTOP_STATE,
        status: 'failed',
        statusMessage: err.message,
        error: err,
        progress: 0,
      });
      throw err;
    }
  }, [analysisMode, config.apiBaseUrl, desktopEnabled, discipline, selectedFile, strictnessLevel, token]);

  const startAnalysis = useCallback(() => {
    if (desktopEnabled) {
      startDesktopAnalysis().catch((error) => {
        console.error('Failed to start desktop analysis', error);
      });
      return;
    }
    startMutation.mutate();
  }, [desktopEnabled, startDesktopAnalysis, startMutation]);

  const cancelAnalysis = useCallback(async () => {
    if (desktopEnabled && desktopState.jobId && window.desktopApi?.tasks) {
      await window.desktopApi.tasks.cancel(desktopState.jobId, 'User requested cancellation');
    }
  }, [desktopEnabled, desktopState.jobId]);

  const reset = useCallback(() => {
    if (desktopEnabled && desktopState.jobId && window.desktopApi?.tasks) {
      window.desktopApi.tasks.cancel(desktopState.jobId, 'Reset requested');
    }
    if (taskId) {
      queryClient.removeQueries({ queryKey: ['analysis-status', taskId] });
    }
    activeDesktopJobIdRef.current = null;
    setDesktopState(INITIAL_DESKTOP_STATE);
    setTaskId(null);
    setSelectedFile(null);
  }, [desktopEnabled, desktopState.jobId, queryClient, taskId]);

  const dropzone = useDropzone({
    onDrop: (files: File[]) => {
      if (files?.length) {
        setSelectedFile(files[0]);
      }
    },
    multiple: false,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
  });

  const progress = desktopEnabled
    ? desktopState.progress
    : statusQuery.data?.progress ?? (startMutation.isPending ? 5 : 0);

  const statusMessage = desktopEnabled
    ? desktopState.statusMessage
    : statusQuery.data?.status_message ?? (startMutation.isPending ? 'Uploading document...' : 'Waiting to start');

  const status = desktopEnabled
    ? ((desktopState.meta as { status?: string } | null)?.status ?? desktopState.status)
    : statusQuery.data?.status;

  const summary = useMemo(() => {
    if (desktopEnabled) {
      if (!desktopState.result) {
        return null;
      }
      const data = desktopState.result;
      const complianceScore = data.analysis?.compliance_score ?? data.overall_score ?? null;
      const findings = data.analysis?.findings ?? data.findings ?? [];
      return {
        complianceScore,
        findings,
        reportHtml: data.report_html,
        raw: data,
      };
    }
    if (!statusQuery.data) {
      return null;
    }
    const data = statusQuery.data;
    const complianceScore = data.analysis?.compliance_score ?? data.overall_score ?? null;
    const findings = data.analysis?.findings ?? data.findings ?? [];
    return {
      complianceScore,
      findings,
      reportHtml: data.report_html,
      raw: data as AnalysisStatus,
    };
  }, [desktopEnabled, desktopState.result, statusQuery.data]);

  const analysisComplete = desktopEnabled
    ? desktopState.status === 'completed'
    : statusQuery.data?.status === 'completed';

  const analysisFailed = desktopEnabled
    ? desktopState.status === 'failed'
    : statusQuery.data?.status === 'failed';

  const error = desktopEnabled
    ? desktopState.error
    : (startMutation.error as Error | null) ?? (statusQuery.error as Error | null) ?? null;

  return {
    selectedFile,
    setSelectedFile,
    dropzone,
    discipline,
    setDiscipline,
    strictness,
    strictnessLevel,
    setStrictness,
    startAnalysis,
    cancelAnalysis,
    isStarting: desktopEnabled ? desktopState.status === 'starting' : startMutation.isPending,
    isPolling: desktopEnabled ? desktopState.isPolling : statusQuery.isFetching,
    taskId,
    progress,
    statusMessage,
    status,
    summary,
    analysisComplete,
    analysisFailed,
    reset,
    error,
    isDesktop: desktopEnabled,
  };
};
