import { api } from '@/api';

export const addCourse = async (course, signal) =>
  api.post('/courses/', course, { signal });

export const getCourses = async (signal) => api.get('/courses/', { signal });
