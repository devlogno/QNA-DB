import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/auth/login'
    } else if (error.response?.status === 403) {
      toast.error('Access denied. Please upgrade your plan.')
    } else if (error.response?.data?.message) {
      toast.error(error.response.data.message)
    } else {
      toast.error('An unexpected error occurred')
    }
    return Promise.reject(error)
  }
)

// API endpoints
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  verifyOTP: (otp) => api.post('/auth/verify-otp', { otp }),
}

export const questionsAPI = {
  getQuestions: (params) => api.get('/api/questions', { params }),
  getQuestion: (id) => api.get(`/api/questions/${id}`),
  saveQuestion: (id) => api.post(`/api/questions/${id}/save`),
  reportQuestion: (id, reason) => api.post(`/api/questions/${id}/report`, { reason }),
  getSolution: (id) => api.get(`/api/questions/${id}/solution`),
  getCQAnswer: (id, subQuestion) => api.get(`/api/questions/${id}/cq-answer/${subQuestion}`),
}

export const categoriesAPI = {
  getLevels: () => api.get('/api/categories/levels'),
  getStreams: (levelId) => api.get(`/api/categories/streams?parent_id=${levelId}`),
  getBoards: (streamId) => api.get(`/api/categories/boards?parent_id=${streamId}`),
  getSubjects: (boardId) => api.get(`/api/categories/subjects?parent_id=${boardId}`),
  getChapters: (subjectId) => api.get(`/api/categories/chapters?parent_id=${subjectId}`),
  getTopics: (chapterId) => api.get(`/api/categories/topics?parent_id=${chapterId}`),
}

export const quizAPI = {
  createQuiz: (settings) => api.post('/api/quiz/create', settings),
  getQuiz: (sessionId) => api.get(`/api/quiz/${sessionId}`),
  submitQuiz: (sessionId, answers) => api.post(`/api/quiz/${sessionId}/submit`, answers),
  getResults: (sessionId) => api.get(`/api/quiz/${sessionId}/results`),
}

export const newsAPI = {
  getNews: () => api.get('/api/news'),
  voteNews: (articleId, voteType) => api.post(`/api/news/${articleId}/vote`, { vote_type: voteType }),
}

export const notesAPI = {
  getNotes: (params) => api.get('/api/notes', { params }),
  createNote: (formData) => api.post('/api/notes', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  updateNote: (id, formData) => api.put(`/api/notes/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteNote: (id) => api.delete(`/api/notes/${id}`),
  deleteNoteImage: (imageId) => api.delete(`/api/notes/images/${imageId}`),
}

export const profileAPI = {
  getProfile: () => api.get('/api/profile'),
  updateProfile: (formData) => api.put('/api/profile', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteAccount: (password) => api.delete('/api/profile', { data: { password } }),
}

export const analyticsAPI = {
  getStats: () => api.get('/api/analytics/stats'),
  getCalendarData: () => api.get('/api/analytics/calendar'),
}

export const leaderboardAPI = {
  getLeaderboard: () => api.get('/api/leaderboard'),
}

export const aiAPI = {
  askQuestion: (formData) => api.post('/api/ai/ask', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getChatHistory: () => api.get('/api/ai/history'),
  deleteChat: (chatId) => api.delete(`/api/ai/history/${chatId}`),
}