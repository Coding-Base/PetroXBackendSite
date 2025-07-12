import { api } from '@/api';

export const createTest = async (admin, signal) =>
  api.post('/api/create-group-test/', admin, { signal });

export const getTests = async (signal) => api.get('/api/history/', { signal });

export const getTest = async (id, signal) =>
  api.get(`/api/history/${id}`, { signal });

export const getTestSession = (sessionId) =>
  api.get(`/api/test-session/${sessionId}/`, { signal });

export const getLeaderBoard = () => api.get('/api/leaderboard/',  { signal });
export const getUserHistory = () => api.get('/api/history/',  { signal });
export const getUserRank = () => api.get('/api/user/rank/',  { signal });
