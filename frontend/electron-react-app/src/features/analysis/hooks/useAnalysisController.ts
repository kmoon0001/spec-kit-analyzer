import { useCallback, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';

import { analyzeDocument, fetchAnalysisStatus, AnalysisStatus } from '../api';

const STRICTNESS_OPTIONS = ['lenient', 'standard', 'strict'] as const;
type StrictnessLevel = 0 | 1 | 2;

export const useAnalysisController = () => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [discipline, setDiscipline] = useState('pt');
  const [analysisMode] = useState('rubric');
  const [strictness, setStrictnessState] = useState<StrictnessLevel>(1);
  const [taskId, setTaskId] = useState<string | null>(null);

  const strictnessLevel = STRICTNESS_OPTIONS[strictness];

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
    enabled: Boolean(taskId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data || data.status !== 'completed') {
        return 1500;
      }
      return false;
    },
  });

  const handleDrop = useCallback((files: File[]) => {
    if (files?.length) {
      setSelectedFile(files[0]);
    }
  }, []);

  const dropzone = useDropzone({
    onDrop: handleDrop,
    multiple: false,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
  });

  const reset = useCallback(() => {
    if (taskId) {
      queryClient.removeQueries({ queryKey: ['analysis-status', taskId] });
    }
    setTaskId(null);
    setSelectedFile(null);
  }, [queryClient, taskId]);

  const progress = statusQuery.data?.progress ?? (startMutation.isPending ? 5 : 0);
  const statusMessage =
    statusQuery.data?.status_message ?? (startMutation.isPending ? 'Uploading document...' : 'Waiting to start');

  const analysisComplete = statusQuery.data?.status === 'completed';
  const analysisFailed = statusQuery.data?.status === 'failed';

  const summary = useMemo(() => {
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
  }, [statusQuery.data]);

  return {
    selectedFile,
    setSelectedFile,
    dropzone,
    discipline,
    setDiscipline,
    strictness,
    strictnessLevel,
    setStrictness,
    startAnalysis: () => startMutation.mutate(),
    isStarting: startMutation.isPending,
    isPolling: statusQuery.isFetching,
    taskId,
    progress,
    statusMessage,
    status: statusQuery.data?.status,
    summary,
    analysisComplete,
    analysisFailed,
    reset,
    error: startMutation.error ?? statusQuery.error ?? null,
  };
};

