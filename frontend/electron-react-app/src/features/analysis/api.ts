import { apiClient } from '../../lib/api/client';

export type AnalysisStartResponse = {
  task_id: string;
  status: string;
};

export type AnalysisStatus = {
  status: 'processing' | 'analyzing' | 'completed' | 'failed';
  status_message?: string;
  progress?: number;
  filename?: string;
  error?: string;
  analysis?: {
    compliance_score?: number;
    findings?: Array<{
      id?: string;
      category?: string;
      description?: string;
      severity?: string | number;
    }>;
    [key: string]: unknown;
  };
  findings?: Array<Record<string, unknown>>;
  overall_score?: number;
  report_html?: string;
  result?: Record<string, unknown>;
  strictness?: string;
};

export type Rubric = {
  id: number;
  name: string;
  discipline: string;
  regulation: string;
  common_pitfalls: string;
  best_practice: string;
  value: number;
};

export const analyzeDocument = async (
  payload: { file: File; discipline: string; analysisMode: string; strictness: 'lenient' | 'standard' | 'strict'; rubric?: string },
): Promise<AnalysisStartResponse> => {
  const formData = new FormData();
  formData.append('file', payload.file);
  formData.append('discipline', payload.discipline);
  formData.append('analysis_mode', payload.analysisMode);
  formData.append('strictness', payload.strictness);
  if (payload.rubric) {
    formData.append('rubric', payload.rubric);
  }

  const { data } = await apiClient.post<AnalysisStartResponse>('/analysis/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const fetchAnalysisStatus = async (taskId: string): Promise<AnalysisStatus> => {
  const { data } = await apiClient.get<AnalysisStatus>(`/analysis/status/${taskId}`);
  return data;
};

export const fetchRubrics = async (): Promise<Rubric[]> => {
  const { data } = await apiClient.get<{ rubrics: Rubric[] }>('/rubrics');
  return data.rubrics;
};
