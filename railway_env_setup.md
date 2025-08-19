# Railway Environment Variables Setup

This document provides the complete list of environment variables needed for the Sentigen Social backend deployment on Railway.

## Critical Authentication Variables

These are **REQUIRED** for authentication to work:

```bash
# Supabase Configuration
SUPABASE_URL=https://lvgrswaemwvmjdawsvdj.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT Authentication (CRITICAL - this is what's missing!)
JWT_SECRET=AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg==
```

## How to Set in Railway

### Method 1: Railway Dashboard
1. Go to https://railway.app
2. Select your project: `sentigen-social-production`
3. Click on the backend service
4. Go to "Variables" tab
5. Add each variable with its value
6. Deploy the changes

### Method 2: Railway CLI
```bash
# Install Railway CLI if not already installed
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Set the critical variables
railway variables set JWT_SECRET="AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg=="

railway variables set SUPABASE_URL="https://lvgrswaemwvmjdawsvdj.supabase.co"

railway variables set SUPABASE_SERVICE_KEY="YOUR_SERVICE_KEY_HERE"

railway variables set SUPABASE_ANON_KEY="YOUR_ANON_KEY_HERE"

# Deploy
railway up
```

## Complete Environment Variables List

### Authentication & Database (Required)
- `JWT_SECRET` - Supabase Legacy JWT Secret
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SUPABASE_ANON_KEY` - Supabase anonymous key

### AI Providers (At least one required)
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `PERPLEXITY_API_KEY` - Perplexity API key
- `GEMINI_API_KEY` - Google Gemini API key

### Social Media (Optional)
- `AYRSHARE_API_KEY` - Ayrshare API key for social posting
- `HEYGEN_API_KEY` - HeyGen API key for video generation
- `COMETAPI_KEY` - CometAPI key for Midjourney

### Application Configuration
- `APP_ENV=production`
- `LOG_LEVEL=info`
- `APP_HOST=0.0.0.0`
- `APP_PORT=$PORT` (Railway provides this)
- `CORS_ORIGINS=https://zyyn.ai,https://www.zyyn.ai`

## Verification

After setting the variables, verify the deployment:

1. Check the Railway logs for startup messages
2. Look for: "JWT_SECRET loaded from environment"
3. Test the health endpoint: `curl https://your-app.up.railway.app/health`
4. Test authentication: Use the test script or frontend

## Common Issues

### "JWT_SECRET not set" Warning
- The JWT_SECRET environment variable is missing or empty
- Set it to the Supabase Legacy JWT Secret

### "sign in required" Error
- User is authenticated on frontend but backend rejects the token
- Usually means JWT_SECRET mismatch between Supabase and Railway

### Token Decode Errors
- The JWT_SECRET doesn't match Supabase's Legacy JWT Secret
- Check Supabase dashboard → Settings → API → JWT Settings → Legacy JWT Secret

## Getting Supabase Keys

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings → API
4. Copy:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_ANON_KEY`
   - service_role key → `SUPABASE_SERVICE_KEY`
5. Go to Settings → API → JWT Settings
6. Copy Legacy JWT Secret → `JWT_SECRET`

## Testing

Use the test script to verify JWT validation:

```bash
cd social-media-module/backend
python test_jwt_validation.py
```

Follow the interactive prompts to test with a real token from the browser.
