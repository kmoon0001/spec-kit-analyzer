import { useQuery, UseQueryOptions } from '@tanstack/react-query';

import { apiClient } from '../lib/api/client';

export interface SystemMetrics {
  cpuPercent: number;
  memoryPercent: number;
  memoryAvailableMb: number;
  timestamp: string;
}

type Options = Pick<UseQueryOptions<SystemMetrics>, 'enabled' | 'staleTime' | 'refetchInterval'>;

export const useSystemMetrics = (options?: Options) => {
  return useQuery<SystemMetrics>({
    queryKey: ['system-metrics'],
    queryFn: async () => {
      const { data } = await apiClient.get<{
        cpu_percent: number;
        memory_percent: number;
        memory_available_mb: number;
        timestamp: string;
      }>('/health/system');

      return {
        cpuPercent: data.cpu_percent,
        memoryPercent: data.memory_percent,
        memoryAvailableMb: data.memory_available_mb,
        timestamp: data.timestamp,
      };
    },
    refetchInterval: 5000,
    staleTime: 4000,
    ...options,
  });
};
