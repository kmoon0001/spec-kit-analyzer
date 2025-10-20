import { useQuery, UseQueryOptions } from "@tanstack/react-query";

import { apiClient } from "../lib/api/client";

interface HealthResponse {
  status: string;
  database?: string;
}

type Options = Pick<UseQueryOptions<HealthResponse>, "enabled">;

export const useHealthStatus = (options?: Options) => {
  return useQuery<HealthResponse>({
    queryKey: ["health-status"],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>("/health");
      return data;
    },
    refetchInterval: 10000,
    ...options,
  });
};
