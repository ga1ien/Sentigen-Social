# 🚀 Deployment Guide

## Quick Start (Development)

### 1. Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account
- API keys for AI providers

### 2. Environment Setup
```bash
# Copy environment template
cp env.template .env

# Copy frontend environment
cp env.template frontend/.env.local

# Edit both files with your actual API keys and configuration
```

### 3. Database Setup
1. Create a new Supabase project
2. Run the SQL migration in your Supabase SQL editor:
   ```sql
   -- Copy content from social-media-module/backend/database/migrations/001_initial_schema.sql
   ```
3. Enable the `vector` extension in Supabase

### 4. Start Development Servers

**Backend:**
```bash
cd social-media-module/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 5. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Production Deployment

### Option 1: Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Manual Deployment

**Backend (FastAPI):**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

**Frontend (Next.js):**
```bash
# Build the application
npm run build

# Start production server
npm start
```

### Option 3: Cloud Deployment

**Vercel (Frontend):**
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

**Railway/Render (Backend):**
1. Connect your GitHub repository
2. Set environment variables
3. Deploy with automatic builds

## Environment Variables

### Required Variables
```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key

# AI Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-key

# Social Media
AYRSHARE_API_KEY=your-ayrshare-key
```

### Optional Variables
```env
# Additional AI providers
PERPLEXITY_API_KEY=pplx-your-key
GEMINI_API_KEY=your-gemini-key
HEYGEN_API_KEY=your-heygen-key
COMETAPI_KEY=your-cometapi-key

# Configuration
DEFAULT_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
DEFAULT_OPENAI_MODEL=gpt-4o
```

## Health Checks

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "ayrshare_connected": true,
  "heygen_connected": true,
  "services": {
    "database": true,
    "ayrshare": true,
    "heygen": true,
    "midjourney": true,
    "openai": true,
    "anthropic": true,
    "perplexity": true,
    "gemini": true
  }
}
```

### Frontend Health Check
Visit http://localhost:3000 - should show the landing page

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
- Check Supabase URL and keys
- Ensure database is accessible
- Verify network connectivity

**2. AI Provider Errors**
- Verify API keys are correct
- Check API quotas and billing
- Ensure models are available

**3. Frontend Build Errors**
- Clear node_modules and reinstall
- Check TypeScript errors
- Verify environment variables

**4. CORS Issues**
- Update CORS_ORIGINS in backend
- Check frontend API_URL configuration

### Logs and Monitoring

**Backend Logs:**
```bash
# Development
python -m uvicorn api.main:app --reload --log-level debug

# Production
tail -f /var/log/app.log
```

**Frontend Logs:**
```bash
# Development
npm run dev

# Production
pm2 logs nextjs-app
```

## Security Checklist

### Production Security
- [ ] Use HTTPS in production
- [ ] Set secure JWT secrets
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts
- [ ] Regular security updates
- [ ] Backup database regularly

### API Key Security
- [ ] Use environment variables only
- [ ] Rotate keys regularly
- [ ] Monitor API usage
- [ ] Set up usage alerts
- [ ] Use least privilege access

## Performance Optimization

### Backend
- Use Redis for caching
- Enable database connection pooling
- Implement background task processing
- Set up CDN for static assets

### Frontend
- Enable Next.js image optimization
- Use proper caching headers
- Implement lazy loading
- Optimize bundle size

## Monitoring

### Recommended Tools
- **Error Tracking**: Sentry
- **Analytics**: PostHog
- **Uptime Monitoring**: UptimeRobot
- **Performance**: New Relic or DataDog

### Key Metrics to Monitor
- API response times
- Database query performance
- AI provider API usage and costs
- User engagement metrics
- Error rates and types

## Scaling Considerations

### Horizontal Scaling
- Use load balancers
- Implement database read replicas
- Use Redis cluster for caching
- Consider microservices architecture

### Vertical Scaling
- Monitor resource usage
- Optimize database queries
- Implement efficient caching
- Use async processing for heavy tasks

## Backup and Recovery

### Database Backups
- Supabase provides automatic backups
- Set up additional backup schedule
- Test restore procedures regularly

### Application Backups
- Version control for code
- Environment variable backups
- Media asset backups

## Support

For deployment issues:
1. Check the logs first
2. Verify environment variables
3. Test health endpoints
4. Check network connectivity
5. Review documentation
6. Create GitHub issue if needed
