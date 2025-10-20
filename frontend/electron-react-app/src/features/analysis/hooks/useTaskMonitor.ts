import { useQuery, UseQueryOptions } from "@tanstack/react-query";

import { apiClient } from "../../../lib/api/client";

export type AnalysisTask = {
  id?: string;
  filename?: string;
  status?: string;
  progress?: number;
  status_message?: string;
};

type Options = Pick<UseQueryOptions<Record<string, AnalysisTask>>, "enabled">;

export const useTaskMonitor = (options?: Options) => {
  return useQuery<Record<string, AnalysisTask>>({
    queryKey: ["analysis-tasks"],
    queryFn: async () => {
      const { data } = await apiClient.get<Record<string, AnalysisTask>>(
        "/analysis/all-tasks",
      );
      return data;
    },
    refetchInterval: 5000,
    ...options,
  });
};
