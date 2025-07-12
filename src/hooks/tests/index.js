// tests/index.js

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTests,
  getTest,
  createTest,
  getTestSession,
  getUserHistory,
  getLeaderBoard
} from '@/services/test.service';
import { toast } from 'sonner';

// Create a new test session
export const useCreateTest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: ['create-test'],
    mutationFn: test => createTest(test).then(res => res),
    onSuccess: () => {
      toast.success('Test created successfully');
      // Invalidate any test list caches
      queryClient.invalidateQueries({ queryKey: ['tests'] });
    },
    onError: err => {
      toast.error(err.response?.data?.detail || 'Failed to create test');
    }
  });
};

// Fetch all available tests
export const useGetTests = () =>
  useQuery({
    queryKey: ['tests'],
    queryFn: () => getTests(),
    staleTime: 5 * 60 * 1000,
    retry: 2,
    onError: err => {
      toast.error('Failed to load tests');
    }
  });

// Fetch a single test by ID
export const useGetTest = id =>
  useQuery({
    queryKey: ['test', id],
    queryFn: () => getTest(id),
    enabled: Boolean(id),
    staleTime: 5 * 60 * 1000,
    retry: 2,
    onError: err => {
      toast.error('Failed to load test details');
    }
  });

// Start or fetch a test session
export const useGetTestSession = (sessionId, enabled) =>
  useQuery({
    queryKey: ['test-session', sessionId],
    queryFn: () => getTestSession(sessionId),
    enabled: enabled && Boolean(sessionId),
    staleTime: 5 * 60 * 1000,
    retry: 2,
    onError: err => {
      toast.error('Failed to load test session');
    }
  });

// Fetch user's test history
export const useGetUserHistory = () =>
  useQuery({
    queryKey: ['history'],
    queryFn: () => getUserHistory(),
    staleTime: 5 * 60 * 1000,
    retry: 2,
    onError: err => {
      toast.error('Failed to load your test history');
    }
  });

// Fetch leaderboard
export const useGetLeaderBoard = () =>
  useQuery({
    queryKey: ['leaderboard'],
    queryFn: () => getLeaderBoard().then(res => res),
    staleTime: 5 * 60 * 1000,
    retry: 2,
    onError: err => {
      toast.error('Failed to load leaderboard');
    }
  });

// Fetch user's rank
export const useGetUserRank = () =>
  useQuery({
    queryKey: ['user-rank'],
    queryFn: () => getUserHistory(), // Replace with getUserRank() if available
    staleTime: 5 * 60 * 1000,
    retry: 2,
    onError: err => {
      toast.error('Failed to load your rank');
    }
  });

