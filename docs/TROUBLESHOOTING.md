# 🔧 Troubleshooting Guide

Common issues and solutions for Sentigen Social platform.

## 🚨 Quick Fixes

### **Application Won't Start**

**Frontend Issues**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+

# Verify environment variables
cat .env.local
```

**Backend Issues**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.11+

# Verify environment variables
python -c "from core.env_config import get_config; print('Config OK')"
```

### **Database Connection Failed**

```bash
# Test Supabase connection
curl -H "apikey: YOUR_ANON_KEY" \
     -H "Authorization: Bearer YOUR_ANON_KEY" \
     "https://YOUR_PROJECT.supabase.co/rest/v1/users?select=*"

# Check if schema is applied
psql "your-connection-string" -c "\dt"

# Apply schema if missing
psql "your-connection-string" -f database/consolidated_schema.sql
```

### **API Errors**

```bash
# Check backend health
curl http://localhost:8000/health

# Verify API keys
curl http://localhost:8000/performance

# Check logs
tail -f logs/app.log
```

## 🔍 Common Error Messages

### **"Module not found" Errors**

**Problem**: Import path issues after cleanup
```
ModuleNotFoundError: No module named 'services.content_intelligence_orchestrator'
```

**Solution**: Update import paths
```python
# OLD (deprecated)
from services.content_intelligence_orchestrator import ContentIntelligenceOrchestrator

# NEW (use unified research API)
from api.unified_research_api import research_service
```

### **"Database table does not exist"**

**Problem**: Missing database schema
```
relation "social_media_posts" does not exist
```

**Solution**: Apply consolidated schema
```bash
# Connect to your Supabase database
psql "your-connection-string" -f database/consolidated_schema.sql

# Verify tables exist
psql "your-connection-string" -c "\dt"
```

### **"Invalid API key" Errors**

**Problem**: Missing or incorrect API keys
```
AuthenticationError: Invalid API key provided
```

**Solution**: Check environment configuration
```bash
# Verify API keys are set
echo $OPENAI_API_KEY
echo $SUPABASE_SERVICE_KEY

# Test API key validity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### **CORS Errors**

**Problem**: Cross-origin request blocked
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution**: Check CORS configuration
```bash
# In backend .env file
CORS_ORIGINS=http://localhost:3000,https://localhost:3000

# Restart backend server
uvicorn api.main:app --reload
```

## 🐛 Debugging Steps

### **1. Check System Status**

```bash
# Verify all services are running
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health  # Backend
curl http://localhost:8000/docs    # API docs
```

### **2. Review Logs**

```bash
# Frontend logs (browser console)
# Open browser dev tools > Console

# Backend logs
tail -f social-media-module/backend/logs/app.log

# Database logs (Supabase dashboard)
# Go to Supabase > Logs > Database
```

### **3. Test Individual Components**

```bash
# Test database connection
python -c "
from database.supabase_client import SupabaseClient
client = SupabaseClient()
print('Database:', client.health_check())
"

# Test AI providers
python -c "
from core.env_config import get_config
config = get_config()
print('OpenAI configured:', bool(config.ai_providers.openai_api_key))
"

# Test social media integration
python -c "
from utils.ayrshare_client import AyrshareClient
client = AyrshareClient()
print('Ayrshare:', client.health_check())
"
```

## 🔧 Performance Issues

### **Slow API Responses**

**Diagnosis**
```bash
# Check performance metrics
curl http://localhost:8000/performance

# Monitor database queries
# Enable query logging in Supabase dashboard
```

**Solutions**
```bash
# Enable caching
REDIS_URL=redis://localhost:6379

# Optimize database queries
# Check database/consolidated_schema.sql for indexes

# Increase worker processes
uvicorn api.main:app --workers 4
```

### **High Memory Usage**

**Diagnosis**
```bash
# Check memory usage
ps aux | grep python
htop  # or top

# Check for memory leaks
python -m memory_profiler your_script.py
```

**Solutions**
```bash
# Limit cache size
MAX_CACHE_SIZE=500

# Optimize worker processes
WORKER_CONCURRENCY=2

# Enable garbage collection
import gc; gc.collect()
```

## 🚀 Deployment Issues

### **Vercel Deployment Fails**

**Common Issues**
```bash
# Build timeout
# Solution: Optimize build process
npm run build --max-old-space-size=4096

# Environment variables missing
# Solution: Add in Vercel dashboard
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

### **Railway Deployment Fails**

**Common Issues**
```bash
# Port binding error
# Solution: Use Railway's PORT variable
APP_PORT=$PORT

# Memory limit exceeded
# Solution: Optimize memory usage or upgrade plan
```

### **Database Migration Issues**

**Problem**: Schema conflicts
```bash
# Check current schema version
SELECT * FROM schema_version;

# Backup before migration
pg_dump "connection-string" > backup.sql

# Apply migration
psql "connection-string" -f database/consolidated_schema.sql
```

## 📊 Monitoring & Alerts

### **Set Up Health Monitoring**

```bash
# Create health check script
#!/bin/bash
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000 || exit 1
```

### **Log Analysis**

```bash
# Find errors in logs
grep -i error logs/app.log

# Monitor API response times
grep "response_time" logs/app.log | tail -20

# Check database connection issues
grep -i "database" logs/app.log
```

## 🆘 Getting Help

### **Self-Diagnosis Checklist**

- [ ] All environment variables are set correctly
- [ ] Database schema is applied and up-to-date
- [ ] API keys are valid and have sufficient quota
- [ ] Network connectivity is working
- [ ] All required services are running
- [ ] Logs don't show critical errors

### **Escalation Steps**

1. **Check Documentation**: Review relevant docs in `/docs/`
2. **Run Verification**: `python scripts/verify_cleanup.py`
3. **Collect Information**:
   - Error messages and stack traces
   - Environment configuration (without secrets)
   - System information (OS, versions)
   - Steps to reproduce the issue

### **Emergency Recovery**

```bash
# Reset to known good state
git stash  # Save current changes
git checkout main  # Return to stable version
git pull origin main  # Get latest stable code

# Restore database from backup
psql "connection-string" < backup.sql

# Restart all services
./dev.sh
```

## 🔍 Advanced Debugging

### **Enable Debug Mode**

```bash
# Backend debug mode
LOG_LEVEL=debug
DEBUG=true

# Frontend debug mode
NEXT_PUBLIC_DEBUG=true
```

### **Database Query Analysis**

```bash
# Enable slow query logging in Supabase
# Dashboard > Settings > Database > Query Performance

# Analyze query performance
EXPLAIN ANALYZE SELECT * FROM social_media_posts WHERE user_id = 'xxx';
```

### **Network Debugging**

```bash
# Test API connectivity
curl -v http://localhost:8000/health

# Check DNS resolution
nslookup your-supabase-url.supabase.co

# Test SSL certificates
openssl s_client -connect your-domain.com:443
```

---

**Still having issues? Check the [Configuration Guide](./CONFIGURATION.md) or review the [Architecture](./ARCHITECTURE.md) for more context.** 🔍
