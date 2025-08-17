# 🚀 AI Social Media Platform API Documentation

## 📋 Overview

The AI Social Media Platform API provides comprehensive endpoints for content generation, social media management, avatar video creation, and analytics. Built with FastAPI, it offers automatic OpenAPI documentation and high-performance async operations.

**Base URL**: `http://localhost:8000` (Development) | `https://sentigen-social-production.up.railway.app` (Production)

**API Version**: `1.0.0`

## 🔐 Authentication

The API uses Supabase authentication with JWT tokens. Include the authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## 📊 System Endpoints

### Health Check
**GET** `/health`

Returns system health status and service availability.

**Response Example**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-17T20:01:50.597976",
  "version": "1.0.0",
  "ayrshare_connected": true,
  "heygen_connected": false,
  "services": {
    "database": true,
    "ayrshare": true,
    "heygen": false,
    "midjourney": false,
    "openai": true,
    "anthropic": true,
    "perplexity": true,
    "gemini": true
  }
}
```

### Performance Metrics
**GET** `/performance`

Returns detailed performance metrics and caching statistics.

**Response Example**:
```json
{
  "timestamp": "2025-08-17T20:01:50.597976",
  "cache": {
    "hits": 0,
    "misses": 0,
    "sets": 0,
    "errors": 0,
    "hit_rate_percent": 0,
    "memory_cache_size": 0,
    "redis_connected": false
  },
  "database": {
    "query_performance": {
      "summary": {
        "total_queries": 0,
        "unique_queries": 0,
        "slow_queries_count": 0,
        "avg_execution_time": 0
      }
    }
  }
}
```

## 📝 Content Generation

### Generate Content
**POST** `/api/content/generate`

Generate AI-powered social media content.

**Request Body**:
```json
{
  "topic": "AI and machine learning trends",
  "platform": "linkedin",
  "tone": "professional",
  "length": "medium",
  "include_hashtags": true,
  "include_emojis": false,
  "target_audience": "tech professionals"
}
```

**Response**:
```json
{
  "content": "Generated content text...",
  "hashtags": ["#AI", "#MachineLearning", "#Tech"],
  "engagement_score": 8.5,
  "platform_optimized": true,
  "word_count": 150,
  "character_count": 890
}
```

### Optimize Content for Platform
**POST** `/api/content/optimize/{platform}`

Optimize existing content for a specific platform.

**Path Parameters**:
- `platform`: Target platform (twitter, linkedin, facebook, instagram)

**Request Body**:
```json
{
  "content": "Original content to optimize",
  "optimization_goals": ["engagement", "reach", "conversion"]
}
```

## 📱 Social Media Posts

### Create Post
**POST** `/api/post`

Create a new social media post.

**Request Body**:
```json
{
  "content": "Your post content",
  "platforms": ["twitter", "linkedin"],
  "media_urls": ["https://example.com/image.jpg"],
  "scheduled_at": "2025-08-18T10:00:00Z",
  "auto_hashtag": true,
  "auto_optimize": true
}
```

### Get All Posts
**GET** `/api/posts`

Retrieve all posts with pagination and filtering.

**Query Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `status`: Filter by status (draft, scheduled, published, failed)
- `platform`: Filter by platform

### Get Post by ID
**GET** `/api/posts/{post_id}`

Retrieve a specific post by ID.

### Update Post
**PUT** `/api/posts/{post_id}`

Update an existing post.

### Publish Post
**POST** `/api/posts/{post_id}/publish`

Immediately publish a scheduled or draft post.

## 🎭 Avatar & Video Generation

### Get Avatar Profiles
**GET** `/api/avatars/profiles`

Retrieve all available avatar profiles.

### Create Avatar Profile
**POST** `/api/avatars/profiles`

Create a new avatar profile.

**Request Body**:
```json
{
  "name": "Professional Avatar",
  "heygen_avatar_id": "avatar_123",
  "voice_id": "voice_456",
  "description": "Professional business avatar",
  "is_active": true
}
```

### Generate Video Script
**POST** `/api/avatars/scripts/generate`

Generate a video script for avatar content.

**Request Body**:
```json
{
  "topic": "Product launch announcement",
  "duration_seconds": 60,
  "tone": "enthusiastic",
  "key_points": ["New features", "Benefits", "Call to action"]
}
```

### Create Avatar Video
**POST** `/api/avatars/videos/create`

Create a video with an avatar.

**Request Body**:
```json
{
  "avatar_profile_id": "profile_123",
  "script_content": "Hello, welcome to our platform...",
  "video_title": "Welcome Video",
  "background_music": true,
  "aspect_ratio": "16:9"
}
```

### Get Video Status
**GET** `/api/avatars/videos/{video_id}/status`

Check the status of video generation.

## 🎨 Media Management

### Upload Media
**POST** `/api/media/upload`

Upload media files (images, videos, documents).

**Request**: Multipart form data
- `file`: Media file
- `tags`: Optional tags (JSON array)
- `description`: Optional description

### Get Media Library
**GET** `/api/media`

Retrieve media library with filtering and pagination.

**Query Parameters**:
- `type`: Filter by media type (image, video, document)
- `tags`: Filter by tags
- `page`: Page number
- `per_page`: Items per page

## 🎯 AI Image Generation

### Generate Image with Midjourney
**POST** `/api/midjourney/image`

Generate images using Midjourney AI.

**Request Body**:
```json
{
  "prompt": "A futuristic cityscape at sunset",
  "style": "photorealistic",
  "aspect_ratio": "16:9",
  "quality": "high"
}
```

### Generate Video with Midjourney
**POST** `/api/midjourney/video`

Generate videos using Midjourney AI.

## 🤖 HeyGen Integration

### Get HeyGen Avatars
**GET** `/api/heygen/avatars`

Retrieve available HeyGen avatars.

### Get HeyGen Voices
**GET** `/api/heygen/voices`

Retrieve available HeyGen voices.

### Create HeyGen Video
**POST** `/api/heygen/video`

Create a video using HeyGen service.

### Get HeyGen Video Status
**GET** `/api/heygen/video/{video_id}`

Check HeyGen video generation status.

## 📈 Analytics & Monitoring

### Avatar Analytics Dashboard
**GET** `/api/avatars/analytics/dashboard`

Get comprehensive avatar usage analytics.

### Avatar Usage Limits
**GET** `/api/avatars/limits`

Check current usage limits and quotas.

## 🔄 Sync Operations

### Sync HeyGen Avatars
**POST** `/api/avatars/sync-heygen`

Synchronize avatar profiles with HeyGen service.

## 📋 Response Formats

### Standard Success Response
```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation completed successfully",
  "timestamp": "2025-08-17T20:01:50.597976"
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": { /* error details */ }
  },
  "timestamp": "2025-08-17T20:01:50.597976"
}
```

### Paginated Response
```json
{
  "data": [ /* array of items */ ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_count": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

## 🚨 Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Invalid or missing authentication |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `SERVICE_UNAVAILABLE` | External service unavailable |
| `INTERNAL_ERROR` | Internal server error |

## 🔧 Rate Limits

- **General API**: 1000 requests per hour per user
- **Content Generation**: 100 requests per hour per user
- **Video Generation**: 10 requests per hour per user
- **Image Generation**: 50 requests per hour per user

## 📚 SDKs and Examples

### Python Example
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Generate content
content_data = {
    "topic": "AI trends",
    "platform": "linkedin",
    "tone": "professional"
}
response = requests.post(
    "http://localhost:8000/api/content/generate",
    json=content_data,
    headers={"Authorization": "Bearer your-token"}
)
print(response.json())
```

### JavaScript Example
```javascript
// Health check
const healthResponse = await fetch('http://localhost:8000/health');
const healthData = await healthResponse.json();
console.log(healthData);

// Generate content
const contentData = {
    topic: 'AI trends',
    platform: 'linkedin',
    tone: 'professional'
};
const contentResponse = await fetch('http://localhost:8000/api/content/generate', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your-token'
    },
    body: JSON.stringify(contentData)
});
const content = await contentResponse.json();
console.log(content);
```

## 🔗 Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## 📞 Support

For API support and questions:
- **Documentation**: [/docs](http://localhost:8000/docs)
- **Health Status**: [/health](http://localhost:8000/health)
- **Performance Metrics**: [/performance](http://localhost:8000/performance)
