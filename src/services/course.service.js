// src/services/course.service.js
import { api } from '@/api';

// Create a new course
export const addCourse = (course, signal) =>
  api
    .post('/api/courses/', course, { signal })
    .then(response => response.data);

// Fetch all courses
export const getCourses = signal =>
  api
    .get('/api/courses/', { signal })
    .then(response => response.data);
