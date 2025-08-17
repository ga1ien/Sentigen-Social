# 🚀 Deployment Guide

## 📋 Overview

This guide covers deploying the AI Social Media Platform to production using Railway (backend) and Vercel (frontend).

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vercel        │    │   Railway       │    │   Supabase      │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Database)    │
│   Next.js       │    │   FastAPI       │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Prerequisites

### Required Tools
```bash
# Install Railway CLI
npm install -g @railway/cli

# Install Vercel CLI
npm install -g vercel

# Verify installations
railway --version
vercel --version
```

### Required Accounts
- [Railway](https://railway.app) - Backend hosting
- [Vercel](https://vercel.com) - Frontend hosting
- [Supabase](https://supabase.com) - Database
- [OpenAI](https://openai.com) - AI services (required)
- [Ayrshare](https://ayrshare.com) - Social media posting (optional)

## 🗄️ Database Setup

### 1. Create Supabase Project
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Create new project
3. Note your project URL and anon key
4. Run the database schema:

```sql
-- Copy and run the contents of database/complete_supabase_schema.sql
-- in your Supabase SQL editor
```

### 2. Configure Row Level Security
The schema includes RLS policies. Ensure they're enabled:

```sql
-- Verify RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

## 📡 Backend Deployment (Railway)

### 1. Setup Railway Project
```bash
# Login to Railway
railway login

# Link to existing project or create new one
railway link
# OR
railway init
```

### 2. Configure Environment Variables
In Railway dashboard, add these environment variables:

```bash
# Core Configuration
ENVIRONMENT=production
LOG_LEVEL=info
PORT=8000

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AI Providers (at minimum OpenAI)
OPENAI_API_KEY=sk-your_openai_key

# Optional: Additional AI providers
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
PERPLEXITY_API_KEY=pplx-your_perplexity_key
GEMINI_API_KEY=your_gemini_key

# Optional: Social Media
AYRSHARE_API_KEY=your_ayrshare_key

# Optional: Video Services
HEYGEN_API_KEY=your_heygen_key
```

### 3. Deploy Backend
```bash
# Quick deployment
./scripts/deploy-backend.sh

# OR manual deployment
cd social-media-module/backend
railway up
```

### 4. Verify Backend Deployment
```bash
# Check health
curl https://your-railway-app.up.railway.app/health

# Check API docs
open https://your-railway-app.up.railway.app/docs
```

## 🌐 Frontend Deployment (Vercel)

### 1. Setup Vercel Project
```bash
# Login to Vercel
vercel login

# Link to existing project or create new one
vercel link
```

### 2. Configure Environment Variables
In Vercel dashboard, add these environment variables:

```bash
# Public Environment Variables
NEXT_PUBLIC_APP_NAME=AI Social Media Platform
NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_AI_GENERATION=true
NEXT_PUBLIC_ENABLE_SCHEDULING=true

# Build Configuration
NEXT_TELEMETRY_DISABLED=1
```

### 3. Deploy Frontend
```bash
# Quick deployment
./scripts/deploy-frontend.sh

# OR manual deployment
vercel --prod
```

## 🚀 Complete Deployment

### Automated Deployment
```bash
# Deploy both backend and frontend
./scripts/deploy-all.sh
```

### Manual Step-by-Step
```bash
# 1. Deploy backend
./scripts/deploy-backend.sh

# 2. Wait for backend to be ready
curl https://your-railway-app.up.railway.app/health

# 3. Deploy frontend
./scripts/deploy-frontend.sh
```

## 🔍 Post-Deployment Verification

### Backend Health Checks
```bash
# System health
curl https://your-railway-app.up.railway.app/health

# Performance metrics
curl https://your-railway-app.up.railway.app/performance

# API documentation
open https://your-railway-app.up.railway.app/docs
```

### Frontend Verification
```bash
# Check if frontend loads
curl -I https://your-vercel-app.vercel.app

# Test API connection from frontend
# Navigate to your frontend URL and check browser console
```

### Database Verification
```bash
# Test database connection
curl -X POST https://your-railway-app.up.railway.app/api/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{"content": "Test post", "platforms": ["twitter"]}'
```

## 🔧 Configuration Management

### Environment Files
- `env.template` - Development template
- `env.production.template` - Production template
- `.env.local` - Local development (not committed)
- `.env.production` - Production values (not committed)

### Security Best Practices
1. **Never commit sensitive keys** to version control
2. **Use different keys** for development and production
3. **Rotate API keys** regularly
4. **Enable 2FA** on all service accounts
5. **Use environment variables** for all configuration

## 📊 Monitoring & Observability

### Railway Monitoring
- **Logs**: Railway dashboard → Deployments → Logs
- **Metrics**: Railway dashboard → Metrics
- **Health**: `/health` endpoint

### Vercel Monitoring
- **Analytics**: Vercel dashboard → Analytics
- **Functions**: Vercel dashboard → Functions
- **Performance**: Built-in Web Vitals

### Custom Monitoring
```bash
# Performance metrics endpoint
curl https://your-railway-app.up.railway.app/performance

# Health check with details
curl https://your-railway-app.up.railway.app/health | jq '.'
```

## 🚨 Troubleshooting

### Common Backend Issues

#### Build Failures
```bash
# Check Railway build logs
railway logs --deployment

# Validate requirements
pip install -r requirements-prod.txt
```

#### Database Connection Issues
```bash
# Test Supabase connection
curl -X GET "https://your-project.supabase.co/rest/v1/users" \
  -H "apikey: your-anon-key"
```

#### Environment Variable Issues
```bash
# Validate configuration
cd social-media-module/backend
python scripts/validate_config.py
```

### Common Frontend Issues

#### Build Failures
```bash
# Check build locally
cd frontend
npm run build

# Check Vercel build logs
vercel logs
```

#### API Connection Issues
```bash
# Test API from frontend
curl https://your-vercel-app.vercel.app/api/health
```

### Performance Issues

#### Backend Optimization
- **Increase worker count**: Set `WEB_CONCURRENCY=4` in Railway
- **Enable Redis caching**: Add `REDIS_URL` environment variable
- **Database connection pooling**: Adjust `DB_POOL_SIZE`

#### Frontend Optimization
- **Enable ISR**: Configure `revalidate` in pages
- **Optimize images**: Use Next.js Image component
- **Bundle analysis**: Run `npm run analyze`

## 🔄 CI/CD Pipeline

### GitHub Actions (Optional)
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway login --token ${{ secrets.RAILWAY_TOKEN }}
          railway up --service backend

  deploy-frontend:
    runs-on: ubuntu-latest
    needs: deploy-backend
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          vercel --token ${{ secrets.VERCEL_TOKEN }} --prod
```

## 📞 Support

### Documentation Links
- **API Docs**: `https://your-railway-app.up.railway.app/docs`
- **Health Status**: `https://your-railway-app.up.railway.app/health`
- **Performance**: `https://your-railway-app.up.railway.app/performance`

### Service Status Pages
- [Railway Status](https://status.railway.app)
- [Vercel Status](https://vercel-status.com)
- [Supabase Status](https://status.supabase.com)

### Quick Commands Reference
```bash
# Backend deployment
./scripts/deploy-backend.sh

# Frontend deployment
./scripts/deploy-frontend.sh

# Complete deployment
./scripts/deploy-all.sh

# Health check
curl https://your-railway-app.up.railway.app/health

# API testing
./social-media-module/backend/scripts/quick_api_test.sh
```
