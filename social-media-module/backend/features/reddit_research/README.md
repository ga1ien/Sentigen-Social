# Reddit Research Feature

> **AI-Powered Reddit Content Research with GPT-5 Mini Integration**

## 🎯 Overview

The Reddit Research feature enables comprehensive analysis of Reddit content using AI. It can research any topic across multiple subreddits, analyze posts and comments with GPT-5 Mini, and generate actionable business intelligence.

## ✨ Features

- 🔍 **Universal Topic Research** - Works with any research topic, not just AI tools
- 🤖 **GPT-5 Mini Analysis** - Real AI analysis with sentiment, relevance, and insights
- 📊 **Flexible Schema** - Consolidated 3-table structure for efficient data storage
- 🎯 **Smart Filtering** - Relevance scoring and keyword extraction
- 📈 **Business Intelligence** - Actionable recommendations and opportunity identification
- 💾 **Supabase Integration** - All findings automatically saved to database

## 🏗️ Architecture

```
features/reddit_research/
├── reddit_ai_research_worker.py    # Main worker class
├── check_supabase_schema.py        # Schema validation tool
├── docs/
│   ├── REDDIT_API_INTEGRATION.md   # API documentation
│   ├── CURRENT_SCHEMA.md           # Generated schema docs
│   └── schema_info.json            # Raw schema metadata
└── schema/
    └── reddit_research_schema.sql  # Complete schema definition
```

## 📊 Database Schema

### Tables

1. **`reddit_research_sessions`** - Research session tracking
2. **`reddit_content`** - Unified posts and comments storage
3. **`reddit_research_insights`** - AI-generated insights and reports

### Key Features
- ✅ **Flexible Design** - Works with any research topic
- ✅ **Rich Metadata** - JSONB fields for extensible data
- ✅ **Performance Optimized** - Comprehensive indexing
- ✅ **Full-Text Search** - PostgreSQL GIN indexes
- ✅ **Audit Trail** - Created/updated timestamps
- ✅ **Data Integrity** - Foreign key constraints and checks

## 🚀 Quick Start

### 1. Initialize Worker

```python
from features.reddit_research.reddit_ai_research_worker import RedditAIResearchWorker

# Initialize with automatic configuration
worker = RedditAIResearchWorker()
```

### 2. Run Research

```python
# Research any topic
session_id = await worker.research_ai_automation_tools(
    workspace_id="your-workspace-id",
    user_id="your-user-id",
    session_name="AI Tools Market Research",
    search_query="AI automation business productivity",
    subreddits=["artificial", "productivity", "Entrepreneur"],
    max_posts_per_subreddit=10
)
```

### 3. Get Results

```python
# Retrieve comprehensive results
results = await worker.get_session_results(session_id)

print(f"Posts analyzed: {results['stats']['total_posts']}")
print(f"Average relevance: {results['stats']['avg_relevance']}")
print(f"Top keywords: {results['stats']['top_keywords']}")
```

## 🔧 Configuration

### Environment Variables

```bash
# Reddit API (Required)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=your-app-name

# OpenAI API (Required)
OPENAI_API_KEY=sk-your-openai-key

# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### Worker Configuration

```python
config = {
    "reddit": {
        "max_posts_per_request": 25,
        "max_comments_per_post": 10,
        "rate_limit_delay": 1.0
    },
    "ai": {
        "model": "gpt-5-mini",
        "max_tokens": 1000,
        "temperature": 0.3
    }
}

worker = RedditAIResearchWorker(config)
```

## 📈 Analysis Capabilities

### Content Analysis
- **Relevance Scoring** (0.0 - 1.0)
- **Sentiment Analysis** (positive/negative/neutral)
- **Keyword Extraction**
- **Entity Recognition**
- **Business Context Identification**

### Insights Generation
- **Trend Analysis**
- **Market Opportunities**
- **Competitive Intelligence**
- **User Sentiment Patterns**
- **Actionable Recommendations**

## 🔍 Example Use Cases

### 1. AI Tools Market Research
```python
session_id = await worker.research_ai_automation_tools(
    workspace_id=workspace_id,
    user_id=user_id,
    session_name="AI Tools Q1 2025 Research",
    search_query="AI automation tools business productivity",
    subreddits=["artificial", "productivity", "SaaS", "Entrepreneur"]
)
```

### 2. Competitor Analysis
```python
session_id = await worker.research_ai_automation_tools(
    workspace_id=workspace_id,
    user_id=user_id,
    session_name="Competitor Sentiment Analysis",
    search_query="clickup vs notion vs airtable",
    subreddits=["productivity", "SaaS", "startups"]
)
```

### 3. Industry Trends
```python
session_id = await worker.research_ai_automation_tools(
    workspace_id=workspace_id,
    user_id=user_id,
    session_name="Remote Work Tools 2025",
    search_query="remote work collaboration tools 2025",
    subreddits=["remotework", "digitalnomad", "productivity"]
)
```

## 🛠️ Development Tools

### Schema Validation
```bash
python features/reddit_research/check_supabase_schema.py
```

### Health Check
```python
# Check all integrations
health = await worker.health_check()
print(f"Reddit API: {health['reddit_api']}")
print(f"OpenAI API: {health['openai_api']}")
print(f"Supabase: {health['supabase']}")
```

## 📊 Performance Metrics

- **Processing Speed**: ~5-10 posts per minute
- **AI Analysis**: GPT-5 Mini with 1-2 second response time
- **Storage**: Efficient JSONB compression for metadata
- **Scalability**: Handles 100+ posts per research session

## 🔒 Security & Privacy

- **Row Level Security** ready (commented in schema)
- **API Key Protection** via environment variables
- **Data Isolation** by workspace_id
- **Audit Logging** with timestamps
- **Content Filtering** for inappropriate content

## 🚨 Rate Limits & Best Practices

### Reddit API Limits
- **60 requests per minute** for OAuth2
- **1 request per second** recommended
- **Built-in rate limiting** in worker

### OpenAI API Limits
- **GPT-5 Mini**: High rate limits
- **Automatic retries** with exponential backoff
- **Token optimization** for cost efficiency

### Best Practices
1. **Batch Processing** - Process multiple posts together
2. **Caching** - Store results to avoid re-analysis
3. **Monitoring** - Use health checks regularly
4. **Error Handling** - Graceful degradation on failures

## 📝 API Reference

See [REDDIT_API_INTEGRATION.md](docs/REDDIT_API_INTEGRATION.md) for detailed API documentation.

## 🔄 Schema Updates

The schema is designed to be backward-compatible. Future updates will:
- Add new columns with defaults
- Extend JSONB fields for new metadata
- Maintain existing indexes and constraints

## 🎯 Roadmap

- [ ] **Real-time Processing** - WebSocket updates for live research
- [ ] **Advanced Analytics** - Trend detection and forecasting
- [ ] **Multi-platform** - Extend to Twitter, LinkedIn, etc.
- [ ] **Custom Models** - Support for fine-tuned AI models
- [ ] **Visualization** - Built-in charts and graphs
- [ ] **Export Features** - PDF reports and CSV exports

---

**Status**: ✅ Production Ready
**Last Updated**: January 16, 2025
**Version**: 1.0.0
