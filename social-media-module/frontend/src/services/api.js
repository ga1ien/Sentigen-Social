import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`Response from ${response.config.url}:`, response.status);
    return response;
  },
  (error) => {
    console.error('Response error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API service methods
export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Get connected accounts
  async getConnectedAccounts() {
    const response = await api.get('/api/accounts');
    return response.data;
  },

  // Create social media post
  async createPost(postData) {
    const response = await api.post('/api/post', postData);
    return response.data;
  },

  // Create post with streaming response
  createPostStream(postData) {
    return new EventSource(
      `${api.defaults.baseURL}/api/post/stream?${new URLSearchParams(postData)}`
    );
  },

  // Get post analytics
  async getPostAnalytics(postId) {
    const response = await api.get(`/api/analytics/${postId}`);
    return response.data;
  },

  // Optimize content for platforms
  async optimizeContent(content, platforms, options = {}) {
    const response = await api.post('/api/optimize', {
      content,
      platforms,
      ...options,
    });
    return response.data;
  },
};

export default api;