import axios from 'axios';

// Use relative path for development
const baseURL = 'https://petroxtestbackend.onrender.com';
export const api = axios.create({
  baseURL: baseURL,
  headers: { 'Content-Type': 'application/json' }
});

// Helper function to get tokens
const getAccessToken = () => localStorage.getItem('access_token');
const getRefreshToken = () => localStorage.getItem('refresh_token');

// Request interceptor to inject token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 error and we haven't already tried to refresh
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getRefreshToken();
        const response = await axios.post(`${baseURL}/api/token/refresh/`, {
          refresh: refreshToken
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);
        originalRequest.headers.Authorization = `Bearer ${access}`;

        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token failed - log user out
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const refreshToken = (refresh) =>
  api.post('api/token/refresh/', { refresh });


export const loginUser = (username, password) =>
  api.post('api/token/', { username, password });



// Courses & Tests
export const fetchCourses = () => api.get('courses/');
export const startTest = (courseId, questionCount, duration) =>
  api.post('start-test/', {
    course_id: courseId,
    question_count: questionCount,
    duration
  });
export const submitTest = (sessionId, answers) =>
  api.post(`submit-test/${sessionId}/`, { answers });
export const fetchTestSession = (sessionId) =>
  api.get(`test-session/${sessionId}/`);

// History
export const fetchHistory = () => api.get('history/');

// Group Test
export const createGroupTest = (payload) =>
  api.post('create-group-test/', payload);

// Leaderboard and rank
export const fetchLeaderboard = () => api.get('leaderboard/');
export const fetchUserHistory = () => api.get('history/');
export const fetchUserRank = () => api.get('user/rank/');

//fetch user upload stats

export const fetchUserUploadStats = () => {
  return axios.get('/api/user/upload-stats/', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
};

export default api;
