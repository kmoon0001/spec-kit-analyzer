import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8001';

export interface ComplianceTrend {
  dates: string[];
  overall_scores: number[];
  frequency_scores: number[];
  goal_scores: number[];
  progress_scores: number[];
}

export interface RiskPrediction {
  audit_risk: {
    current: number;
    trend: string;
    factors: Array<{
      name: string;
      impact: number;
      trend: string;
    }>;
  };
  compliance_forecast: {
    '30_days': number;
    '60_days': number;
    '90_days': number;
    confidence: number;
  };
  recommendations: Array<{
    priority: 'high' | 'medium' | 'low';
    action: string;
    impact: string;
    effort: string;
  }>;
}

export interface BenchmarkData {
  industry_averages: {
    overall_compliance: number;
    frequency_documentation: number;
    goal_specificity: number;
    progress_tracking: number;
  };
  your_performance: {
    overall_compliance: number;
    frequency_documentation: number;
    goal_specificity: number;
    progress_tracking: number;
  };
  percentile_ranking: number;
  top_performers: {
    overall_compliance: number;
    frequency_documentation: number;
    goal_specificity: number;
    progress_tracking: number;
  };
}

export interface AdvancedAnalyticsData {
  compliance_trends: ComplianceTrend;
  key_metrics: {
    overall_compliance: number;
    documentation_quality: number;
    risk_score: number;
    efficiency_index: number;
  };
  category_breakdown: Array<{
    name: string;
    score: number;
    color: string;
  }>;
}

export const fetchAdvancedAnalytics = async (timeRange: string): Promise<AdvancedAnalyticsData> => {
  const response = await axios.get(`${API_BASE_URL}/analytics/advanced`, {
    params: { time_range: timeRange },
    headers: {
      Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
    },
  });
  return response.data;
};

export const fetchPredictiveAnalytics = async (): Promise<RiskPrediction> => {
  const response = await axios.get(`${API_BASE_URL}/analytics/predictive`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
    },
  });
  return response.data;
};

export const fetchBenchmarkData = async (): Promise<BenchmarkData> => {
  const response = await axios.get(`${API_BASE_URL}/analytics/benchmarks`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
    },
  });
  return response.data;
};

export interface MetaAnalyticsData {
  organizational_metrics: {
    total_users: number;
    avg_compliance_score: number;
    total_findings: number;
    total_analyses: number;
    discipline_breakdown: Record<string, {
      avg_compliance_score: number;
      user_count: number;
    }>;
    team_habit_breakdown: Record<string, {
      habit_number: number;
      habit_name: string;
      percentage: number;
    }>;
  };
  training_needs: Array<{
    habit_name: string;
    percentage_of_findings: number;
    priority: 'high' | 'medium' | 'low';
    affected_users: number;
    training_focus: string;
  }>;
  team_trends: Array<{
    week: number;
    avg_compliance_score: number;
    total_findings: number;
  }>;
  benchmarks: {
    total_users_in_benchmark: number;
    compliance_score_percentiles: {
      p25: number;
      p50: number;
      p75: number;
      p90: number;
    };
  };
  insights: Array<{
    title: string;
    description: string;
    recommendation: string;
    level: 'positive' | 'concern' | 'action_required' | 'neutral';
  }>;
}

export const fetchMetaAnalytics = async (daysBack: number, discipline?: string): Promise<MetaAnalyticsData> => {
  const params = new URLSearchParams({
    days_back: daysBack.toString(),
  });

  if (discipline && discipline !== 'All Disciplines') {
    params.append('discipline', discipline);
  }

  const response = await axios.get(`${API_BASE_URL}/meta-analytics?${params}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
    },
  });
  return response.data;
};