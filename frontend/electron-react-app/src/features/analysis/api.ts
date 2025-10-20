import { apiClient } from "../../lib/api/client";

export type AnalysisStartResponse = {
  task_id: string;
  status: string;
};

export type AnalysisStatus = {
  status: "processing" | "analyzing" | "completed" | "failed";
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
      habit_info?: {
        habit_id: string;
        habit_number: number;
        name: string;
        explanation: string;
        confidence: number;
      };
    }>;
    habits_insights?: Array<{
      habit: string;
      recommendation: string;
      confidence: number;
    }>;
    [key: string]: unknown;
  };
  findings?: Array<Record<string, unknown>>;
  overall_score?: number;
  report_html?: string;
  result?: Record<string, unknown>;
  strictness?: string;
  rag_enhanced?: boolean;
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

export const analyzeDocument = async (payload: {
  file: File;
  discipline: string;
  analysisMode: string;
  strictness: "ultra_fast" | "balanced" | "thorough" | "clinical_grade";
  rubric?: string;
}): Promise<AnalysisStartResponse> => {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("discipline", payload.discipline);
  formData.append("analysis_mode", payload.analysisMode);
  formData.append("strictness", payload.strictness);
  if (payload.rubric) {
    formData.append("rubric", payload.rubric);
  }

  const { data } = await apiClient.post<AnalysisStartResponse>(
    "/analysis/analyze",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );
  return data;
};

export const fetchAnalysisStatus = async (
  taskId: string,
): Promise<AnalysisStatus> => {
  const { data } = await apiClient.get<AnalysisStatus>(
    `/analysis/status/${taskId}`,
  );
  return data;
};

export const fetchRubrics = async (): Promise<Rubric[]> => {
  const { data } = await apiClient.get<{ rubrics: Rubric[] }>("/rubrics");
  return data.rubrics;
};

// Strictness Level API
export type StrictnessLevel = {
  level_name: string;
  accuracy_threshold: number;
  confidence_threshold: number;
  fact_checking: string;
  ensemble_agreement: number;
  validation_passes: number;
  processing_time_target: string;
  use_cached_results: boolean;
  description: string;
};

export const fetchStrictnessLevels = async (): Promise<
  Record<string, StrictnessLevel>
> => {
  const { data } = await apiClient.get<Record<string, StrictnessLevel>>(
    "/api/strictness/levels",
  );
  return data;
};

export const getCurrentStrictnessLevel = async (): Promise<{
  current_level: string;
  level_config: StrictnessLevel;
  performance_metrics: Record<string, unknown>;
  success: boolean;
}> => {
  const { data } = await apiClient.get("/api/strictness/current");
  return data;
};

export const setStrictnessLevel = async (
  levelName: string,
): Promise<{
  current_level: string;
  level_config: StrictnessLevel;
  performance_metrics: Record<string, unknown>;
  success: boolean;
}> => {
  const { data } = await apiClient.post("/api/strictness/set", {
    level_name: levelName,
  });
  return data;
};
