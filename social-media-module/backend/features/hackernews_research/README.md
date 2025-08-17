# 🔍 Hacker News Research Tool

A comprehensive, production-ready research tool for collecting and analyzing Hacker News content using AI. This tool provides deep insights into technology trends, startup ecosystem, developer community discussions, and business intelligence from the HN community.

## 🎯 **Why Hacker News?**

- **🔓 No API Keys Required**: Completely open API with no authentication
- **⚡ No Rate Limits**: Scrape as fast as you want
- **🔄 Real-time Data**: Updates every few seconds
- **💎 High-Quality Discussions**: Tech leaders, founders, engineers
- **🧹 Clean Structure**: Perfect for AI ingestion
- **🎪 Rich Content Types**: Stories, Ask HN, Show HN, comments with deep threads

## 🏗️ **Architecture Overview**

This tool follows the **microservices pattern** - it's completely independent and can be deployed separately from other research tools.

```
hackernews-research-tool/
├── 📋 Configuration System      # User-configurable research parameters
├── 🔄 Two-Stage Data Pipeline   # Raw collection + AI analysis
├── 🤖 AI Analysis Engine        # GPT-5 Mini comprehensive analysis
├── 📅 Automated Scheduling      # Daily/weekly/bi-weekly runs
├── 🌐 REST API                  # Frontend integration
├── 🖥️  CLI Interface            # Command-line tools
└── 🔧 Background Execution      # Independent background processing
```

## 🚀 **Key Features**

### **📊 Comprehensive Data Collection**
- **Story Types**: Top, New, Best, Ask HN, Show HN, Job posts
- **Deep Comment Trees**: Recursive comment collection with configurable depth
- **Smart Filtering**: Score, comment count, time range, topic relevance
- **Parallel Processing**: Fast collection using ThreadPoolExecutor
- **Full Context Preservation**: Complete raw data for AI analysis

### **🤖 Advanced AI Analysis**
- **GPT-5 Mini Integration**: Comprehensive story and comment analysis
- **Technology Intelligence**: Mentioned technologies, tools, frameworks
- **Business Intelligence**: Startup insights, market trends, funding patterns
- **Developer Community**: Technical discussions, best practices, challenges
- **Sentiment Analysis**: Community sentiment and engagement patterns
- **Innovation Analysis**: Disruption potential, market opportunities

### **⚙️ User-Configurable Research**
- **Flexible Topics**: Any search topics or focus areas
- **Story Type Selection**: Choose which HN sections to monitor
- **Volume Control**: Configure stories per type, comments per story
- **Quality Filters**: Minimum scores, comment counts, time ranges
- **Analysis Depth**: Basic, Standard, or Comprehensive AI analysis

### **📅 Automated Scheduling**
- **Multiple Frequencies**: Daily, weekly, bi-weekly, monthly, custom cron
- **Time Zone Support**: Run at optimal times for your region
- **Background Execution**: Independent of IDE or terminal sessions
- **Robust Process Management**: PID tracking, graceful shutdown, error recovery

## 📁 **File Structure**

```
hackernews_research/
├── 📄 __init__.py                          # Package initialization
├── ⚙️  hackernews_research_config.py       # Configuration system
├── 🔄 cli_hackernews_scraper_raw.py        # Raw data collection
├── 🤖 cli_hackernews_analyzer.py           # AI analysis worker
├── 🌐 hackernews_research_api.py           # REST API endpoints
├── 🔧 run_hackernews_background.sh         # Background execution manager
├── 📚 README.md                            # This documentation
├── 📁 user_configs/                        # User configuration storage
├── 📁 raw_data/                            # Raw collected data
├── 📁 analyzed_data/                       # AI-analyzed results
└── 📁 pids/                                # Process ID files
```

## 🛠️ **Installation & Setup**

### **Prerequisites**
- Python 3.8+
- Virtual environment activated
- OpenAI API key for GPT-5 Mini

### **Environment Variables**
```bash
# Required for AI analysis
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Supabase for data storage
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
```

### **Quick Start**
```bash
# 1. Navigate to the tool directory
cd social-media-module/backend/features/hackernews_research

# 2. Create sample configurations
python hackernews_research_config.py --create-samples

# 3. Test raw data collection (quick test)
python cli_hackernews_scraper_raw.py

# 4. Run AI analysis on collected data
python cli_hackernews_analyzer.py --latest

# 5. Start background pipeline
./run_hackernews_background.sh pipeline
```

## 📋 **Configuration System**

### **Sample Configuration**
```python
tech_trends_config = HackerNewsResearchConfig(
    user_id="user_001",
    workspace_id="workspace_001",
    config_name="tech_trends",
    description="Daily HN research on technology trends",

    hackernews_config=HackerNewsConfig(
        story_types=[HNStoryType.TOP, HNStoryType.ASK, HNStoryType.SHOW],
        search_topics=["AI", "startup", "technology", "programming"],
        max_stories_per_type=12,
        max_comments_per_story=25,
        min_score=50,
        min_comments=10,
        comment_depth=2,
        time_range_hours=24
    ),

    analysis_depth=AnalysisDepth.COMPREHENSIVE,
    schedule=ResearchSchedule(
        frequency=ResearchFrequency.DAILY,
        time_of_day="08:00",
        timezone="America/New_York"
    ),

    auto_run_enabled=True,
    focus_areas=["business_intelligence", "trend_analysis"],
    generate_content_ideas=True
)
```

### **Configuration Management**
```bash
# Create sample configurations
python hackernews_research_config.py --create-samples

# List user configurations
python hackernews_research_config.py --list user_001

# Show specific configuration
python hackernews_research_config.py --show user_001 tech_trends
```

## 🔄 **Two-Stage Data Pipeline**

### **Stage 1: Raw Data Collection**
```bash
# Collect raw HN data (fast, no AI analysis)
python cli_hackernews_scraper_raw.py

# Background raw collection
./run_hackernews_background.sh raw
```

**What it collects:**
- Complete story metadata (title, URL, text, author, score, time)
- Full comment trees with replies (configurable depth)
- Story type classification (top, ask, show, etc.)
- Priority scoring for analysis
- Raw HTML cleaning and text extraction

### **Stage 2: AI Analysis**
```bash
# Analyze latest raw dataset
python cli_hackernews_analyzer.py --latest

# Analyze specific dataset
python cli_hackernews_analyzer.py --dataset raw_hackernews_dataset_20240116_143022.json

# Background analysis
./run_hackernews_background.sh analyze
```

**AI Analysis Includes:**
- **Technology Relevance**: Scoring and categorization
- **Business Intelligence**: Market trends, startup insights
- **Community Sentiment**: Engagement patterns, controversy detection
- **Innovation Analysis**: Disruption potential, adoption barriers
- **Actionable Insights**: For developers, entrepreneurs, investors
- **Content Opportunities**: Blog ideas, discussion topics

## 🔧 **Background Execution**

### **Background Runner Commands**
```bash
# Start raw data collection in background
./run_hackernews_background.sh raw

# Start AI analysis in background
./run_hackernews_background.sh analyze

# Run complete pipeline (raw → analysis)
./run_hackernews_background.sh pipeline

# Check status of all processes
./run_hackernews_background.sh status

# View recent logs
./run_hackernews_background.sh logs

# Stop all background processes
./run_hackernews_background.sh stop
```

### **Process Management**
- **PID Tracking**: Each process gets a unique PID file
- **Graceful Shutdown**: SIGTERM handling for clean stops
- **Log Management**: Timestamped logs for each run
- **Error Recovery**: Automatic cleanup of dead processes
- **Status Monitoring**: Real-time process status checking

## 🌐 **REST API**

### **Start API Server**
```bash
# Start HN research API on port 8002
python hackernews_research_api.py

# Or with uvicorn
uvicorn hackernews_research_api:app --host 0.0.0.0 --port 8002
```

### **API Endpoints**

#### **Configuration Management**
```bash
# Create new research configuration
POST /configs
{
  "user_id": "user_001",
  "config_name": "tech_trends",
  "hackernews_config": {
    "story_types": ["top", "ask"],
    "search_topics": ["AI", "startup"],
    "max_stories_per_type": 10
  }
}

# List user configurations
GET /configs/{user_id}

# Get specific configuration
GET /configs/{user_id}/{config_name}

# Update configuration
PUT /configs/{user_id}/{config_name}

# Delete configuration
DELETE /configs/{user_id}/{config_name}
```

#### **Job Management**
```bash
# Trigger research job
POST /jobs/trigger
{
  "job_type": "pipeline",  # raw, analyze, or pipeline
  "config_name": "tech_trends",
  "priority": "normal"
}

# Get job status
GET /jobs/status/{job_id}

# List active jobs
GET /jobs/active

# Get job history
GET /jobs/history?limit=20
```

#### **Health Check**
```bash
# API health check
GET /health
```

## 📊 **Data Output Examples**

### **Raw Data Structure**
```json
{
  "collection_session": {
    "timestamp": "2024-01-16T14:30:22",
    "total_stories_collected": 25,
    "collection_mode": "raw_data_only"
  },
  "raw_stories": [
    {
      "collection_info": {
        "collected_at": "2024-01-16T14:30:22",
        "story_type": "top",
        "story_index": 1
      },
      "hackernews_data": {
        "id": 44927244,
        "title": "Dev Compass – Programming Philosophy Quiz",
        "url": "https://devcompass.io/",
        "author": "username",
        "score": 156,
        "time": 1705419022,
        "descendants": 42
      },
      "comments": [
        {
          "id": 44927301,
          "author": "commenter",
          "text": "This is really interesting...",
          "replies": [...]
        }
      ],
      "analysis_status": {
        "ready_for_analysis": true,
        "analysis_priority": "high"
      }
    }
  ]
}
```

### **AI Analysis Output**
```json
{
  "analysis_session": {
    "analyzed_at": "2024-01-16T14:35:15",
    "analysis_version": "hackernews_comprehensive_v1"
  },
  "analyzed_stories": [
    {
      "ai_analysis": {
        "relevance_analysis": {
          "tech_relevance_score": 0.85,
          "business_relevance_score": 0.72,
          "target_audience": ["developers", "entrepreneurs"],
          "tech_categories": ["web dev", "tools"]
        },
        "sentiment_analysis": {
          "overall_sentiment": "positive",
          "sentiment_score": 0.6,
          "community_engagement": "high"
        },
        "technology_intelligence": {
          "mentioned_technologies": ["React", "Node.js"],
          "mentioned_companies": ["Google", "Microsoft"],
          "emerging_trends": ["AI-powered development"]
        },
        "business_intelligence": {
          "startup_insights": ["Product-market fit indicators"],
          "market_trends": ["Developer tool adoption"],
          "competitive_landscape": ["Similar tools analysis"]
        },
        "actionable_insights": {
          "for_developers": ["Learning opportunities"],
          "for_entrepreneurs": ["Market gaps identified"],
          "for_content_creators": ["Trending topics"]
        }
      }
    }
  ],
  "analysis_summary": {
    "hackernews_intelligence": {
      "avg_tech_relevance": 0.78,
      "sentiment_distribution": {"positive": 15, "neutral": 8, "negative": 2},
      "top_technologies_mentioned": ["AI", "React", "Python"],
      "high_relevance_stories": 12
    }
  }
}
```

## 🔗 **Integration with Orchestration API**

This HN research tool integrates seamlessly with the multi-source orchestration API:

```javascript
// Frontend integration example
const response = await fetch('/research/multi-source', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user_001',
    research_name: 'weekly_tech_research',
    enabled_sources: ['reddit', 'hackernews'],
    hackernews_config: {
      story_types: ['top', 'ask', 'show'],
      search_topics: ['AI', 'startup', 'technology'],
      max_stories_per_type: 10
    },
    analysis_depth: 'comprehensive'
  })
});
```

## 📈 **Performance & Scaling**

### **Performance Characteristics**
- **Raw Collection**: ~50 stories with comments in 2-3 minutes
- **AI Analysis**: ~25 stories with comprehensive analysis in 3-5 minutes
- **Memory Usage**: ~100-200MB during collection, ~300-500MB during analysis
- **Storage**: ~1-5MB per dataset (JSON format)

### **Scaling Options**
- **Horizontal**: Multiple instances for different users/topics
- **Vertical**: Increase max_workers for faster parallel processing
- **Distributed**: Use message queues for large-scale processing
- **Caching**: Cache HN API responses to reduce API calls

## 🛡️ **Error Handling & Reliability**

### **Robust Error Recovery**
- **API Failures**: Automatic retry with exponential backoff
- **Partial Data**: Save partial results if some stories fail
- **Process Crashes**: PID cleanup and graceful restart
- **Network Issues**: Timeout handling and connection pooling
- **AI Failures**: Continue processing other stories if one fails

### **Monitoring & Logging**
- **Structured Logging**: Timestamped, categorized log entries
- **Progress Tracking**: Real-time progress indicators
- **Error Reporting**: Detailed error messages with context
- **Performance Metrics**: Collection and analysis timing
- **Health Checks**: API endpoint for service health monitoring

## 🔮 **Future Enhancements**

### **Planned Features**
- **🔍 Advanced Search**: Boolean operators, date ranges, author filtering
- **📊 Trend Analysis**: Historical trend tracking and prediction
- **🎯 Smart Recommendations**: AI-powered topic suggestions
- **📱 Real-time Notifications**: Alerts for high-impact stories
- **🔗 Cross-Reference**: Link related stories across time
- **📈 Analytics Dashboard**: Visual insights and metrics
- **🤝 Collaboration**: Shared configurations and insights
- **🔌 Webhooks**: Real-time integration with external systems

### **Integration Opportunities**
- **Supabase Storage**: Persistent data storage and querying
- **Slack/Discord**: Automated insights delivery
- **Content Management**: Direct publishing to blogs/social media
- **Business Intelligence**: Integration with BI tools
- **Machine Learning**: Custom model training on HN data

## 🎯 **Use Cases**

### **For Developers**
- **Technology Trends**: Track emerging technologies and frameworks
- **Best Practices**: Learn from community discussions
- **Career Insights**: Understand market demands and opportunities
- **Tool Discovery**: Find new development tools and libraries

### **For Entrepreneurs**
- **Market Research**: Identify market gaps and opportunities
- **Competitive Intelligence**: Monitor competitor discussions
- **Product Validation**: Gauge community interest in ideas
- **Funding Trends**: Track startup funding patterns

### **For Content Creators**
- **Topic Ideas**: Generate content based on trending discussions
- **Community Insights**: Understand developer pain points
- **Engagement Strategies**: Learn what resonates with tech audience
- **Trend Prediction**: Stay ahead of technology curves

### **For Investors**
- **Deal Flow**: Identify promising startups and technologies
- **Market Intelligence**: Understand technology adoption patterns
- **Due Diligence**: Research companies and technologies
- **Trend Analysis**: Spot emerging investment opportunities

## 🤝 **Contributing**

This tool is part of a larger microservices architecture. Each source tool is independent, making it easy to contribute to specific components:

1. **Fork the repository**
2. **Focus on HN-specific features** in the `hackernews_research/` directory
3. **Follow the established patterns** for configuration, CLI, and API
4. **Add comprehensive tests** for new functionality
5. **Update documentation** for any changes
6. **Submit pull requests** with clear descriptions

## 📄 **License**

This project is part of the Sentigen Social platform. Please refer to the main project license for usage terms.

---

**🔍 The Hacker News Research Tool provides comprehensive, AI-powered insights into the technology and startup ecosystem through systematic analysis of HN content. It's designed for production use with robust error handling, scalable architecture, and flexible configuration options.**
