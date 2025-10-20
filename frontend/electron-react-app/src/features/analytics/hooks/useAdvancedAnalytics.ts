import { useQuery } from "@tanstack/react-query";
import { useAppStore } from "../../../store/useAppStore";
import {
  fetchAdvancedAnalytics,
  fetchPredictiveAnalytics,
  fetchBenchmarkData,
} from "../api";

export const useAdvancedAnalytics = (timeRange: string = "Last 30 Days") => {
  const token = useAppStore((state) => state.auth.token);

  const analyticsQuery = useQuery({
    queryKey: ["advanced-analytics", timeRange],
    queryFn: () => fetchAdvancedAnalytics(timeRange),
    enabled: Boolean(token),
    staleTime: 60000, // 1 minute
  });

  const predictiveQuery = useQuery({
    queryKey: ["predictive-analytics"],
    queryFn: fetchPredictiveAnalytics,
    enabled: Boolean(token),
    staleTime: 300000, // 5 minutes
  });

  const benchmarkQuery = useQuery({
    queryKey: ["benchmark-data"],
    queryFn: fetchBenchmarkData,
    enabled: Boolean(token),
    staleTime: 600000, // 10 minutes
  });

  return {
    analytics: analyticsQuery.data,
    predictive: predictiveQuery.data,
    benchmarks: benchmarkQuery.data,
    isLoading:
      analyticsQuery.isLoading ||
      predictiveQuery.isLoading ||
      benchmarkQuery.isLoading,
    isError:
      analyticsQuery.isError ||
      predictiveQuery.isError ||
      benchmarkQuery.isError,
    refetch: () => {
      analyticsQuery.refetch();
      predictiveQuery.refetch();
      benchmarkQuery.refetch();
    },
  };
};
