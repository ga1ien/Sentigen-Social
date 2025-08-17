# ⚙️ Configuration Guide

Complete guide for configuring Sentigen Social for development and production environments.

## 📋 Environment Variables

### **Frontend Configuration (.env.local)**

```bash
# Supabase Configuration (Required)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...your-anon-key

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### **Backend Configuration (.env)**

```bash
# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
APP_ENV=development  # development | staging | production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=info

# Security
JWT_SECRET=your-super-secret-jwt-key-change-in-production
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# =============================================================================
# DATABASE (Supabase) - REQUIRED
# =============================================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...your-service-key
SUPABASE_ANON_KEY=eyJ...your-anon-key

# =============================================================================
# AI PROVIDERS
# =============================================================================

# OpenAI (Primary - REQUIRED)
OPENAI_API_KEY=sk-...your-openai-key
DEFAULT_OPENAI_MODEL=gpt-4o
OPENAI_ORG_ID=org-...your-org-id

# Anthropic Claude (Optional)
ANTHROPIC_API_KEY=sk-ant-...your-anthropic-key
DEFAULT_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Perplexity (Research - Optional)
PERPLEXITY_API_KEY=pplx-...your-perplexity-key
PERPLEXITY_MODEL=llama-3.1-sonar-small-128k-online

# Google Gemini (Optional)
GEMINI_API_KEY=AI...your-gemini-key
GOOGLE_VEO3_MODEL=gemini-2.0-flash-exp

# =============================================================================
# VIDEO & AVATAR GENERATION (Optional)
# =============================================================================

# HeyGen (Avatar Videos)
HEYGEN_API_KEY=your-heygen-api-key
HEYGEN_BASE_URL=https://api.heygen.com/v2

# Midjourney (Images via CometAPI)
COMETAPI_KEY=your-comet-api-key
COMETAPI_BASE_URL=https://api.cometapi.com

# =============================================================================
# SOCIAL MEDIA INTEGRATION (Optional)
# =============================================================================

# Ayrshare (Multi-platform Posting)
AYRSHARE_API_KEY=your-ayrshare-api-key
AYRSHARE_BASE_URL=https://app.ayrshare.com/api

# =============================================================================
# PERFORMANCE & CACHING (Optional)
# =============================================================================

# Redis (Caching)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password

# Cache Settings
CACHE_TTL=300
MAX_CACHE_SIZE=1000

# =============================================================================
# MONITORING (Production)
# =============================================================================

# Sentry (Error Tracking)
SENTRY_DSN=https://...your-sentry-dsn

# Feature Flags
ENABLE_RESEARCH_TOOLS=true
ENABLE_AVATAR_VIDEOS=true
ENABLE_SOCIAL_POSTING=true
ENABLE_ANALYTICS=true
```

## 🔧 Service Configuration

### **Supabase Setup**

1. **Create Project**
   ```bash
   # Visit https://supabase.com/dashboard
   # Create new project
   # Note your project URL and keys
   ```

2. **Apply Database Schema**
   ```bash
   # Use the SQL editor in Supabase dashboard
   # Or connect via psql and run:
   psql -d "your-connection-string" -f database/consolidated_schema.sql
   ```

3. **Configure Authentication**
   - Enable email authentication
   - Set up OAuth providers (optional)
   - Configure redirect URLs

### **OpenAI Setup**

1. **Get API Key**
   ```bash
   # Visit https://platform.openai.com/api-keys
   # Create new API key
   # Set usage limits and billing
   ```

2. **Configure Models**
   ```bash
   DEFAULT_OPENAI_MODEL=gpt-4o        # Recommended
   # Alternative: gpt-3.5-turbo (cheaper)
   ```

### **Ayrshare Setup (Social Media)**

1. **Create Account**
   ```bash
   # Visit https://ayrshare.com
   # Sign up and verify email
   # Connect your social media accounts
   ```

2. **Get API Key**
   ```bash
   # Go to API Keys section
   # Generate new API key
   # Test connection with a post
   ```

### **HeyGen Setup (Avatar Videos)**

1. **Create Account**
   ```bash
   # Visit https://heygen.com
   # Sign up for API access
   # Choose subscription plan
   ```

2. **Configure Avatars**
   ```bash
   # Upload or select avatars
   # Configure voice settings
   # Test video generation
   ```

## 🚀 Deployment Configuration

### **Development Environment**
```bash
APP_ENV=development
LOG_LEVEL=debug
ENABLE_SWAGGER_UI=true
ENABLE_CORS_ALL=true
```

### **Staging Environment**
```bash
APP_ENV=staging
LOG_LEVEL=info
ENABLE_SWAGGER_UI=true
ENABLE_CORS_ALL=false
```

### **Production Environment**
```bash
APP_ENV=production
LOG_LEVEL=warning
ENABLE_SWAGGER_UI=false
ENABLE_CORS_ALL=false
DEBUG=false
```

## 🔒 Security Configuration

### **JWT Configuration**
```bash
# Generate secure JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Set appropriate expiration
JWT_EXPIRATION=24h  # 24 hours
```

### **CORS Configuration**
```bash
# Development
CORS_ORIGINS=http://localhost:3000

# Production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### **Rate Limiting**
```bash
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds
```

## 📊 Monitoring Configuration

### **Logging**
```bash
# Log levels: debug, info, warning, error, critical
LOG_LEVEL=info

# Structured logging format
LOG_FORMAT=json  # json | text
```

### **Health Checks**
```bash
# Health check endpoints
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_TIMEOUT=30  # seconds
```

### **Performance Monitoring**
```bash
PERFORMANCE_MONITORING=true
METRICS_COLLECTION=true
SLOW_QUERY_THRESHOLD=1000  # milliseconds
```

## 🔧 Advanced Configuration

### **Database Optimization**
```bash
# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30

# Query optimization
ENABLE_QUERY_CACHE=true
QUERY_CACHE_TTL=300
```

### **Worker Configuration**
```bash
# Background workers
WORKER_CONCURRENCY=4
WORKER_TIMEOUT=300
WORKER_RETRY_ATTEMPTS=3
```

### **File Storage**
```bash
# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-media-bucket
```

## 🆘 Troubleshooting

### **Common Issues**

1. **Database Connection Failed**
   ```bash
   # Check Supabase URL and keys
   # Verify network connectivity
   # Check firewall settings
   ```

2. **OpenAI API Errors**
   ```bash
   # Verify API key is valid
   # Check usage limits and billing
   # Ensure model name is correct
   ```

3. **CORS Errors**
   ```bash
   # Check CORS_ORIGINS setting
   # Verify frontend URL matches
   # Check protocol (http vs https)
   ```

### **Validation Commands**
```bash
# Test configuration
python social-media-module/backend/scripts/validate_config.py

# Test database connection
python -c "from database.supabase_client import SupabaseClient; print('DB OK')"

# Test API endpoints
curl http://localhost:8000/health
```

---

*Proper configuration is key to a smooth deployment! 🔑*
