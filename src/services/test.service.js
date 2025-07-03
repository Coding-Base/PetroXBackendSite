import { api } from '@/api';

export const createTest = async (admin, signal) =>
  api.post('/create-group-test/', admin, { signal });

export const getTests = async (signal) => api.get('/history/', { signal });

export const getTest = async (id, signal) =>
  api.get(`/history/${id}`, { signal });

export const getTestSession = (sessionId) =>
  api.get(`/test-session/${sessionId}/`, { signal });

export const getLeaderBoard = () => api.get('leaderboard/',  { signal });
export const getUserHistory = () => api.get('history/',  { signal });
export const getUserRank = () => api.get('user/rank/',  { signal });
