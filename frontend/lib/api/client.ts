import axios, { AxiosInstance, AxiosError } from 'axios';
import { toast } from 'react-hot-toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && originalRequest) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = '/login';
      }
    }

    // Show error toast for other errors
    if (error.response?.data?.detail) {
      toast.error(error.response.data.detail);
    } else if (error.message) {
      toast.error(error.message);
    }

    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Auth
  auth: {
    login: (email: string, password: string) =>
      apiClient.post('/auth/login', { email, password, device_name: 'web' }),
    
    register: (data: {
      email: string;
      password: string;
      full_name: string;
      role: string;
    }) => apiClient.post('/auth/register', data),
    
    logout: () => apiClient.post('/auth/logout'),
    
    me: () => apiClient.get('/auth/me'),
    
    refresh: (refreshToken: string) =>
      apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
  },

  // Learner
  learner: {
    profile: () => apiClient.get('/learner/profile'),
    progress: () => apiClient.get('/learner/progress'),
    streak: () => apiClient.get('/learner/streak'),
    badges: () => apiClient.get('/learner/badges'),
    leaderboard: () => apiClient.get('/learner/leaderboard'),
    
    lesson: (lessonId: number) => apiClient.get(`/learner/lessons/${lessonId}`),
    
    completeLesson: (lessonId: number, data: {
      score: number;
      time_spent_seconds: number;
      exercise_results: any[];
    }) => apiClient.post(`/learner/lessons/${lessonId}/complete`, data),
    
    signPractice: (signId: number) =>
      apiClient.get(`/learner/signs/practice/${signId}`),
    
    submitSignPractice: (signId: number, performance: any) =>
      apiClient.post(`/learner/signs/practice/${signId}/submit`, performance),
  },

  // Content
  content: {
    zones: () => apiClient.get('/content/zones'),
    zoneQuests: (zoneId: number) => apiClient.get(`/content/zones/${zoneId}/quests`),
    questLessons: (questId: number) => apiClient.get(`/content/quests/${questId}/lessons`),
    lesson: (lessonId: number) => apiClient.get(`/content/lessons/${lessonId}`),
    
    searchSigns: (params: {
      q?: string;
      category?: string;
      difficulty?: number;
      limit?: number;
    }) => apiClient.get('/content/signs/search', { params }),
    
    sign: (signId: number) => apiClient.get(`/content/signs/${signId}`),
    
    stories: (difficulty?: number) =>
      apiClient.get('/content/stories', { params: { difficulty } }),
    
    story: (storyId: number) => apiClient.get(`/content/stories/${storyId}`),
  },

  // Teacher
  teacher: {
    students: (params?: { grade?: number; at_risk_only?: boolean }) =>
      apiClient.get('/teacher/class/students', { params }),
    
    sloHeatmap: (grade?: number) =>
      apiClient.get('/teacher/class/slo-heatmap', { params: { grade } }),
    
    studentProgress: (studentId: string) =>
      apiClient.get(`/teacher/student/${studentId}/progress`),
    
    atRiskStudents: () => apiClient.get('/teacher/class/at-risk'),
    
    classAnalytics: () => apiClient.get('/teacher/analytics/class'),
    
    assignLesson: (data: {
      lesson_id: number;
      student_ids: string[];
      due_date?: string;
    }) => apiClient.post('/teacher/class/assign-lesson', data),
  },

  // ML
  ml: {
    detectSign: (imageBase64: string, topK: number = 5) =>
      apiClient.post('/ml/detect-sign', { image_base64: imageBase64, top_k: topK }),
    
    translate: (
      text: string,
      sourceLang: 'ksl' | 'eng' | 'swa',
      targetLang: 'ksl' | 'eng' | 'swa'
    ) => apiClient.post('/ml/translate', {
      text,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
    
    compareSigns: (
      userKeypoints: number[][],
      imaraKeypoints: number[][],
      signId: number
    ) => apiClient.post('/ml/compare-signs', {
      user_keypoints: userKeypoints,
      imara_keypoints: imaraKeypoints,
      sign_id: signId,
    }),
  },
};

export default apiClient;
