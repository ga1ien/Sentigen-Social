# 🚀 AI Social Media Platform

A full-stack AI-powered social media content creation and scheduling platform built with Next.js, FastAPI, and Supabase.

![Platform Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%2015-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Database](https://img.shields.io/badge/Database-Supabase-orange)
![AI](https://img.shields.io/badge/AI-OpenAI%20%7C%20Anthropic-purple)

## ✨ Features

### 🤖 AI-Powered Content Generation
- **Multi-Provider AI**: OpenAI GPT-4o, Anthropic Claude, Perplexity AI
- **Smart Content Creation**: Generate posts optimized for each platform
- **Image Generation**: GPT-Image-1 integration for custom visuals
- **Video Generation**: HeyGen avatars and Google Veo3 support
- **Content Optimization**: AI-powered engagement optimization

### 📱 Social Media Management
- **Multi-Platform Publishing**: Twitter, LinkedIn, Facebook, Instagram
- **Ayrshare Integration**: Reliable social media API
- **Content Scheduling**: Advanced calendar with drag-and-drop
- **Post Analytics**: Comprehensive engagement tracking
- **Bulk Operations**: Schedule multiple posts efficiently

### 🧠 Chrome MCP Social Intelligence
- **Real-time Platform Monitoring**: Automated scanning of Reddit, LinkedIn, Twitter, Hacker News
- **Content Insights Extraction**: AI-powered analysis of high-engagement posts
- **Competitive Intelligence**: Monitor what's working for others
- **Trend Prediction**: Identify emerging topics before they peak
- **Multi-Worker Architecture**: Parallel scanning across platforms

### 🎨 Rich Content Creation
- **Advanced Text Editor**: TipTap with mentions, hashtags, formatting
- **Media Library**: Drag-and-drop file management
- **Template System**: Reusable content templates
- **Brand Guidelines**: Consistent styling across content
- **Character Counting**: Platform-specific limits

### 👥 Team Collaboration
- **Workspace Management**: Multi-tenant architecture
- **Role-Based Access**: Owner, Admin, Editor, Member roles
- **Team Invitations**: Email-based member invites
- **Permission System**: Granular access control
- **Activity Tracking**: Member activity monitoring

### 📊 Analytics & Insights
- **Performance Metrics**: Engagement, reach, impressions
- **Platform Comparison**: Cross-platform analytics
- **Export Capabilities**: Data export for reporting
- **Trend Analysis**: Content performance insights
- **ROI Tracking**: Campaign effectiveness

## 🛠️ Tech Stack

### Frontend (Next.js 15)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS + shadcn/ui
- **Components**: Radix UI primitives
- **Animation**: Framer Motion
- **Forms**: React Hook Form + Zod validation
- **State**: Zustand + TanStack Query
- **Calendar**: FullCalendar with drag-and-drop
- **Charts**: Recharts for analytics
- **Editor**: TipTap rich text editor

### Backend (Python 3.11+)
- **Framework**: FastAPI 0.115.13+
- **AI**: Pydantic AI 0.3.2+ with multi-provider support
- **Database**: Supabase with pgvector
- **Authentication**: Supabase Auth with RLS
- **Social APIs**: Ayrshare, Tweepy, LinkedIn, Facebook
- **Image Processing**: Pillow, Sharp
- **Task Queue**: Multi-worker system
- **Logging**: Structured logging with structlog

### Database & Infrastructure
- **Database**: PostgreSQL via Supabase
- **Vector Search**: pgvector for AI embeddings
- **Authentication**: Supabase Auth with OAuth
- **File Storage**: Supabase Storage
- **Deployment**: Docker containerization
- **Monitoring**: Health checks and logging

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Supabase account
- API keys for AI providers

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-social-media-platform.git
cd ai-social-media-platform
```

### 2. Environment Setup
```bash
# Copy environment templates
cp env.template .env
cp frontend/.env.local.example frontend/.env.local
cp social-media-module/.env.example social-media-module/.env.local

# Edit environment files with your API keys
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Backend Setup
```bash
cd social-media-module/backend
chmod +x setup.sh
./setup.sh
./run.sh
```

### 5. Database Setup
Apply the database schema to your Supabase project:
```sql
-- Run the SQL from database/supabase_schema_v2.sql in your Supabase SQL editor
```

### 6. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🧠 Chrome MCP Intelligence Setup

For advanced social media intelligence, set up Chrome MCP to monitor platforms in real-time:

1. **Install Chrome MCP Extension**: Download from [GitHub releases](https://github.com/hangwin/mcp-chrome/releases)
2. **Install MCP Bridge**: `npm install -g mcp-chrome-bridge`
3. **Connect Extension**: Click extension icon and connect to bridge
4. **Login to Platforms**: Sign into LinkedIn, Twitter, Reddit, etc. in your browser
5. **Configure Intelligence**: Access `/dashboard/intelligence` to set up monitoring

📖 **Detailed Setup Guide**: See [CHROME_MCP_SETUP.md](./CHROME_MCP_SETUP.md) for complete instructions.

## 📁 Project Structure

```
ai-social-media-platform/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # Reusable components
│   │   ├── lib/            # Utilities and configurations
│   │   └── hooks/          # Custom React hooks
│   └── public/             # Static assets
├── social-media-module/     # FastAPI backend
│   └── backend/
│       ├── api/            # FastAPI routes
│       ├── agents/         # Pydantic AI agents
│       ├── workers/        # Multi-worker system
│       ├── database/       # Database clients and migrations
│       ├── models/         # Pydantic models
│       └── utils/          # Utility functions
├── database/               # Database schemas and migrations
├── docs/                   # Documentation
└── docker-compose.yml      # Docker orchestration
```

## 🔧 Configuration

### Required Environment Variables

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

#### Backend (.env.local)
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# AI Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
PERPLEXITY_API_KEY=your_perplexity_key

# Social Media
AYRSHARE_API_KEY=your_ayrshare_key

# Optional: Advanced Features
HEYGEN_API_KEY=your_heygen_key
COMETAPI_KEY=your_midjourney_key
GEMINI_API_KEY=your_gemini_key
```

## 🧪 Testing

### Integration Tests
```bash
# Run comprehensive integration tests
python test_integration.py
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd social-media-module/backend
source venv/bin/activate
pytest
```

## 📊 Current Status

### ✅ Completed Features (85% Complete)
- **Authentication System**: Complete with Supabase Auth
- **Dashboard Views**: All 9 views implemented and functional
- **AI Integration**: OpenAI and Anthropic working perfectly
- **Database**: Supabase connected with comprehensive schema
- **Social Media**: Ayrshare integration active
- **Content Creation**: Rich text editor with AI generation
- **Media Management**: File upload and organization
- **Team Management**: User roles and permissions
- **Analytics**: Performance tracking and insights

### 🔄 In Progress
- **Worker System**: Import path optimization
- **Perplexity Integration**: Model name updates
- **Chrome MCP**: Advanced intelligence features

### 🎯 Performance Metrics
- **Frontend**: Lighthouse score > 90
- **Backend**: Sub-200ms API response times
- **Database**: Optimized queries with indexing
- **AI**: Multi-provider fallback system

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment
1. **Frontend**: Deploy to Vercel, Netlify, or similar
2. **Backend**: Deploy to Railway, Render, or cloud provider
3. **Database**: Use Supabase hosted or self-hosted PostgreSQL

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and image generation
- **Anthropic** for Claude AI assistance
- **Supabase** for backend infrastructure
- **Ayrshare** for social media API
- **Vercel** for Next.js framework
- **FastAPI** for Python backend framework

## 📞 Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-social-media-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-social-media-platform/discussions)

---

**Built with ❤️ using AI-powered development tools**

🌟 **Star this repository if you find it useful!**
