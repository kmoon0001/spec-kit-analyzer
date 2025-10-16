import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '../../../store/useAppStore';
import { fetchMetaAnalytics } from '../api';

export const useMetaAnalytics = (daysBack: number = 90, discipline?: string) => {
  const token = useAppStore((state) => state.auth.token);

  return useQuery({
    queryKey: ['meta-analytics', daysBack, discipline],
    queryFn: () => fetchMetaAnalytics(daysBack, discipline),
    enabled: Boolean(token),
    staleTime: 300000, // 5 minutes
  });
};