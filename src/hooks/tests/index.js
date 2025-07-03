import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getTests,
  getTest,
  createTest,
  getTestSession,
  getUserHistory,
  getLeaderBoard
} from '@/services/test.service';
import { toast } from 'sonner';

export const useCreateTest = () => {
  return useMutation({
    mutationFn: (test) => createTest(test),
    mutationKey: ['create-test'],
    onSuccess: () => {
      toast.success('history created successfully');
    }
  });
};

export const useGetTests = () => {
  return useQuery({
    queryKey: ['tests'],
    queryFn: () => getTests(),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: 2
  });
};
export const useGetTestSession = (sessionId, shouldEnable) => {
  return useQuery({
    queryKey: ['test-session', sessionId],
    queryFn: (sessionId) => getTestSession(sessionId),
    enabled: shouldEnable,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: 2
  });
};

export const useGetTest = (id) => {
  return useQuery({
    queryKey: ['history', id],
    queryFn: () => getTest(id),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: 2
  });
};

export const useGetLeaderBoard = () => {
  return useQuery({
    queryKey: ['history-leaderboard'],
    queryFn: () => getLeaderBoard(),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: 2
  });
};
export const useGetUserRank = () => {
  return useQuery({
    queryKey: ['history-rank'],
    queryFn: () => getUserHistory(),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: 2
  });
};