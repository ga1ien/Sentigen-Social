import axios from 'axios'
import { env } from '@/lib/env'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // In a real app, you'd get the token from Supabase auth
    const token = 'mock-jwt-token' // This would come from Supabase session
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// API endpoints
export const apiClient = {
  // Health check
  health: () => api.get('/health'),

  // Content generation
  generateContent: (data: {
    prompt: string
    content_type: string
    platforms: string[]
    tone: string
    length: string
    include_hashtags: boolean
    include_emojis: boolean
    ai_provider: string
  }) => api.post('/api/content/generate', data),

  optimizeContent: (platform: string, content: string) => 
    api.post(`/api/content/optimize/${platform}`, { content }),

  // Posts
  createPost: (data: {
    content: string
    content_type: string
    platforms: string[]
    media_asset_ids?: string[]
    scheduled_at?: string
    tags?: string[]
    campaign_id?: string
  }) => api.post('/api/posts', data),

  getPosts: (params?: {
    page?: number
    per_page?: number
    status?: string
    platform?: string
  }) => api.get('/api/posts', { params }),

  getPost: (id: string) => api.get(`/api/posts/${id}`),

  updatePost: (id: string, data: {
    content?: string
    platforms?: string[]
    media_asset_ids?: string[]
    scheduled_at?: string
    status?: string
    tags?: string[]
  }) => api.put(`/api/posts/${id}`, data),

  deletePost: (id: string) => api.delete(`/api/posts/${id}`),

  publishPost: (id: string) => api.post(`/api/posts/${id}/publish`),

  // Media
  uploadMedia: (file: File, altText?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (altText) {
      formData.append('alt_text', altText)
    }
    return api.post('/api/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  getMedia: () => api.get('/api/media'),

  // AI Tools
  generateHeyGenVideo: (data: {
    script: string
    avatar_id?: string
    voice_id?: string
  }) => api.post('/api/heygen/video', data),

  getHeyGenVideo: (videoId: string) => api.get(`/api/heygen/video/${videoId}`),

  getHeyGenAvatars: () => api.get('/api/heygen/avatars'),

  getHeyGenVoices: () => api.get('/api/heygen/voices'),

  generateMidjourneyImage: (data: {
    prompt: string
    aspect_ratio?: string
    style?: string
    quality?: string
  }) => api.post('/api/midjourney/image', data),

  generateMidjourneyVideo: (data: {
    prompt: string
    source_image?: string
    video_type?: string
    motion?: string
    animate_mode?: string
  }) => api.post('/api/midjourney/video', data),

  getMidjourneyTask: (taskId: string) => api.get(`/api/midjourney/task/${taskId}`),

  upscaleMidjourneyImage: (taskId: string, index: number) => 
    api.post(`/api/midjourney/upscale/${taskId}`, { index }),
}

export default api
