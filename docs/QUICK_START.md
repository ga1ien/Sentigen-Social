# 🚀 Quick Start Guide

Get Sentigen Social up and running in 15 minutes.

## 📋 Prerequisites

- **Node.js 18+** and npm
- **Python 3.11+**
- **Supabase account** (free tier works)
- **OpenAI API key** (required)

## ⚡ 5-Minute Setup

### 1. Clone and Install
```bash
git clone <repository-url>
cd Sentigen-Social

# Install frontend dependencies
cd frontend && npm install

# Install backend dependencies
cd ../social-media-module/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Frontend environment
cd ../../frontend
cp .env.example .env.local
# Edit .env.local with your Supabase credentials

# Backend environment
cd ../social-media-module/backend
cp config/production.env.template .env
# Edit .env with your API keys
```

### 3. Setup Database
```bash
# Apply the database schema to your Supabase project
psql -d "your-supabase-connection-string" -f database/master_database_schema.sql
```

### 4. Start Development Servers
```bash
# Terminal 1: Frontend
cd frontend && npm run dev

# Terminal 2: Backend
cd social-media-module/backend
source venv/bin/activate
uvicorn api.main:app --reload
```

### 5. Verify Setup
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔑 Required API Keys

### Essential (Required)
- **Supabase**: Database and authentication
- **OpenAI**: AI content generation

### Optional (Enhanced Features)
- **Ayrshare**: Social media posting
- **HeyGen**: Avatar video generation
- **Anthropic**: Alternative AI provider

## 🎯 Next Steps

1. **Create your first post** in the dashboard
2. **Configure social media accounts** in settings
3. **Explore AI tools** in the AI Tools section
4. **Set up research workflows** for content ideas

## 🆘 Need Help?

- **Issues**: Check [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md)
- **Development**: See [`DEVELOPMENT_GUIDE.md`](./DEVELOPMENT_GUIDE.md)
- **Deployment**: Read [`DEPLOYMENT.md`](./DEPLOYMENT.md)

---

**Ready to create amazing content! 🎉**
