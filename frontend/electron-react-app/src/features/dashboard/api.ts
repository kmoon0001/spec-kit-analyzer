import { apiClient } from '../../lib/api/client';

export type DashboardStatistics = {
  total_documents_analyzed: number;
  overall_compliance_score: number;
  compliance_by_category: Record<string, { average_score: number; document_count: number }>;
  last_updated: string;
  error?: string;
};

export type DashboardOverview = {
  ai_health: Record<string, { status: string; details: string }>;
  recent_activity: unknown[];
  system_metrics: { cpu_usage: number; memory_usage: number };
};

const camelCaseStatistics = (payload: DashboardStatistics) => ({
  totalDocumentsAnalyzed: payload.total_documents_analyzed,
  overallComplianceScore: payload.overall_compliance_score,
  complianceByCategory: payload.compliance_by_category,
  lastUpdated: payload.last_updated,
  error: payload.error,
});

export const fetchDashboardStatistics = async () => {
  const { data } = await apiClient.get<DashboardStatistics>('/dashboard/statistics');
  return camelCaseStatistics(data);
};

export const fetchDashboardOverview = async () => {
  const { data } = await apiClient.get<DashboardOverview>('/dashboard/overview');
  return {
    aiHealth: data.ai_health,
    recentActivity: data.recent_activity,
    systemMetrics: data.system_metrics,
  };
};
