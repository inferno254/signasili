import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { toast } from 'react-hot-toast';

export function useProgress() {
  return useQuery({
    queryKey: ['progress'],
    queryFn: async () => {
      const response = await api.learner.progress();
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useStreak() {
  return useQuery({
    queryKey: ['streak'],
    queryFn: async () => {
      const response = await api.learner.streak();
      return response.data;
    },
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useBadges() {
  return useQuery({
    queryKey: ['badges'],
    queryFn: async () => {
      const response = await api.learner.badges();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useLeaderboard() {
  return useQuery({
    queryKey: ['leaderboard'],
    queryFn: async () => {
      const response = await api.learner.leaderboard();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useCompleteLesson() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      lessonId,
      data,
    }: {
      lessonId: number;
      data: {
        score: number;
        time_spent_seconds: number;
        exercise_results: any[];
      };
    }) => {
      const response = await api.learner.completeLesson(lessonId, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['progress'] });
      queryClient.invalidateQueries({ queryKey: ['streak'] });
      queryClient.invalidateQueries({ queryKey: ['badges'] });
      
      // Show success message
      if (data.xp_earned) {
        toast.success(`+${data.xp_earned} XP earned!`);
      }
      
      if (data.new_badges?.length > 0) {
        data.new_badges.forEach((badge: any) => {
          toast.success(`Badge earned: ${badge.name}!`, {
            icon: '🏆',
          });
        });
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to complete lesson');
    },
  });
}
