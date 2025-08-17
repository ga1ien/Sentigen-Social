# 🔧 Environment Setup Guide

## Overview

This guide provides comprehensive instructions for setting up environment variables for the Sentigen Social platform. We've standardized all environment configuration into a single, unified template.

## 📁 File Structure

```
Sentigen-Social/
├── env.unified.template          # ✅ SINGLE SOURCE OF TRUTH
├── frontend/.env.local           # Frontend-specific variables
└── .env                         # Your actual environment file (not in git)
```

## 🚀 Quick Setup

### 1. Copy the Unified Template
```bash
cp env.unified.template .env
```

### 2. Edit Your Configuration
Open `.env` and fill in your actual values:

```bash
# Required - Get from Supabase project settings
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...your-actual-service-key
SUPABASE_ANON_KEY=eyJ...your-actual-anon-key

# Required - At least one AI provider
OPENAI_API_KEY=sk-...your-actual-openai-key

# Required - Generate strong secret
JWT_SECRET=$(openssl rand -base64 32)
```

### 3. Setup Frontend Environment
```bash
# Copy frontend variables
cp .env frontend/.env.local

# Edit frontend/.env.local to only include NEXT_PUBLIC_* variables
```

## 🔑 Required Variables

### Database (Required)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...
```

### AI Provider (At least one required)
```bash
# Option 1: OpenAI (Recommended)
OPENAI_API_KEY=sk-...

# Option 2: Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Option 3: Both for redundancy
```

### Security (Required for production)
```bash
JWT_SECRET=your-super-secret-key-here
```

## 🎯 Optional Services

### Social Media Posting
```bash
AYRSHARE_API_KEY=your-ayrshare-key
```

### Avatar Videos
```bash
HEYGEN_API_KEY=your-heygen-key
```

### Image Generation
```bash
COMETAPI_KEY=your-cometapi-key
```

### Research Tools
```bash
PERPLEXITY_API_KEY=pplx-your-key
```

## 🌍 Environment-Specific Setup

### Development
```bash
APP_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,https://localhost:3000
```

### Production
```bash
APP_ENV=production
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
CORS_ORIGINS=https://your-frontend.vercel.app
JWT_SECRET=$(openssl rand -base64 32)  # Generate strong secret
```

## 🔍 Validation

The platform includes built-in validation:

### Backend Validation
- Type-safe configuration with `env_config.py`
- Automatic validation on startup
- Clear error messages for missing variables

### Frontend Validation
- Schema validation with `@t3-oss/env-nextjs`
- Build-time validation
- Runtime type safety

## 🛠️ Configuration Tools

### Check Configuration Status
```bash
# Backend validation
cd social-media-module/backend
python -c "from core.env_config import get_config; print(get_config().validate())"

# Frontend validation
cd frontend
npm run build  # Will fail if env vars are invalid
```

### Generate JWT Secret
```bash
openssl rand -base64 32
```

### Validate Supabase Connection
```bash
curl -H "apikey: YOUR_ANON_KEY" "YOUR_SUPABASE_URL/rest/v1/"
```

## 🚨 Common Issues

### "Configuration validation failed"
1. Check all required variables are set
2. Verify Supabase URLs start with `https://`
3. Ensure JWT_SECRET is set for production
4. Confirm at least one AI provider is configured

### Frontend can't connect to backend
1. Check `NEXT_PUBLIC_API_URL` matches backend URL
2. Verify `CORS_ORIGINS` includes frontend URL
3. Ensure both use same Supabase project

### AI features not working
1. Verify at least one AI provider API key is set
2. Check API key format (OpenAI: `sk-...`, Anthropic: `sk-ant-...`)
3. Confirm API keys have sufficient credits/permissions

## 🔐 Security Best Practices

### Development
- Use separate API keys from production
- Keep `.env` files out of version control
- Use localhost URLs only

### Production
- Generate strong JWT secrets (`openssl rand -base64 32`)
- Use HTTPS URLs only
- Restrict CORS origins to your domains
- Rotate API keys regularly
- Use environment-specific API keys

### API Key Management
- Store production keys in secure environment (Railway, Vercel, etc.)
- Never commit actual keys to git
- Use different keys for different environments
- Monitor API usage and set up alerts

## 📊 Monitoring Configuration

### Required for Production
```bash
# Error tracking
SENTRY_DSN=https://...your-sentry-dsn

# Performance monitoring
ANALYTICS_ENABLED=true

# Caching
REDIS_URL=redis://your-redis-instance:6379
```

## 🔄 Migration from Old Templates

If you're upgrading from the old multiple template system:

1. **Backup existing configuration**
   ```bash
   cp .env .env.backup
   ```

2. **Use the unified template**
   ```bash
   cp env.unified.template .env
   ```

3. **Migrate your values**
   - Copy your actual API keys from `.env.backup`
   - Update variable names if needed (see migration table below)

4. **Test configuration**
   ```bash
   # Test backend
   cd social-media-module/backend && python -c "from core.env_config import get_config; get_config()"

   # Test frontend
   cd frontend && npm run build
   ```

### Variable Name Migration

| Old Name | New Name |
|----------|----------|
| `SUPABASE_SERVICE_ROLE_KEY` | `SUPABASE_SERVICE_KEY` |
| `ENVIRONMENT` | `APP_ENV` |
| `HOST` | `APP_HOST` |
| `PORT` | `APP_PORT` |

## 📞 Support

For additional help:
- Check `docs/TROUBLESHOOTING.md`
- Review `docs/CONFIGURATION.md`
- See validation errors in application logs
- Ensure all services are properly configured

## ✅ Verification Checklist

Before deploying:

- [ ] All required variables are set
- [ ] Supabase connection works
- [ ] At least one AI provider configured
- [ ] JWT secret is strong (production)
- [ ] CORS origins are correct
- [ ] Frontend can connect to backend
- [ ] All optional services work as expected
- [ ] Configuration validation passes
- [ ] No sensitive data in version control
