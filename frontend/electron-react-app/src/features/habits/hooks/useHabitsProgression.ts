import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '../../../store/useAppStore';
import { fetchHabitsProgression, fetchHabitsAchievements } from '../api';

export const useHabitsProgression = () => {
  const token = useAppStore((state) => state.auth.token);

  const progressionQuery = useQuery({
    queryKey: ['habits-progression'],
    queryFn: fetchHabitsProgression,
    enabled: Boolean(token),
    staleTime: 300000, // 5 minutes
  });

  const achievementsQuery = useQuery({
    queryKey: ['habits-achievements'],
    queryFn: fetchHabitsAchievements,
    enabled: Boolean(token),
    staleTime: 300000, // 5 minutes
  });

  return {
    progression: progressionQuery.data,
    achievements: achievementsQuery.data,
    isLoading: progressionQuery.isLoading || achievementsQuery.isLoading,
    isError: progressionQuery.isError || achievementsQuery.isError,
    refetch: () => {
      progressionQuery.refetch();
      achievementsQuery.refetch();
    },
  };
};