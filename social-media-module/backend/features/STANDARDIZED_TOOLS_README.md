# 🔧 Standardized Research Tools

**Version:** 1.0
**Date:** January 16, 2025
**Compliance:** Project Server Standards v1.0

## 🎯 **Overview**

All research tools have been standardized to comply with **Project Server Standards v1.0**, ensuring:

- **Pydantic AI v0.3.2+** agent framework
- **Snake_case** naming conventions throughout
- **Async/await** patterns for all I/O operations
- **Supabase with asyncpg** for database operations
- **Structured logging** with `structlog`
- **Environment variable management** with `dotenv`
- **Consistent CLI interfaces** and error handling

## 📁 **File Structure**

```
features/
├── STANDARDIZED_TOOL_TEMPLATE.py          # Base template for all tools
├── archive/                               # Original tools (preserved)
│   ├── reddit_research/
│   ├── github_research/
│   ├── hackernews_research/
│   └── google_trends_research/
├── reddit_research/
│   └── cli_reddit_standardized.py         # ✅ Standardized Reddit tool
├── github_research/
│   └── cli_github_standardized.py         # ✅ Standardized GitHub tool
├── hackernews_research/
│   └── cli_hackernews_standardized.py     # ✅ Standardized Hacker News tool
└── google_trends_research/
    └── cli_google_trends_standardized.py  # ✅ Standardized Google Trends tool
```

## 🚀 **Usage Examples**

### **Reddit Research**
```bash
# Basic usage
python cli_reddit_standardized.py --query "AI automation tools"

# Advanced usage
python cli_reddit_standardized.py \
  --query "machine learning" \
  --max-items 20 \
  --analysis-depth comprehensive \
  --config custom_config.json
```

### **GitHub Research**
```bash
# Basic usage
python cli_github_standardized.py --query "AI automation"

# Advanced usage
python cli_github_standardized.py \
  --query "language:python stars:>100" \
  --max-items 15 \
  --analysis-depth standard
```

### **Hacker News Research**
```bash
# Basic usage
python cli_hackernews_standardized.py --query "startup trends"

# Advanced usage
python cli_hackernews_standardized.py \
  --query "AI tools" \
  --max-items 25 \
  --analysis-depth comprehensive
```

### **Google Trends Research**
```bash
# Basic usage
python cli_google_trends_standardized.py --query "AI automation"

# Advanced usage
python cli_google_trends_standardized.py \
  --query "machine learning" \
  --max-items 10 \
  --analysis-depth standard
```

## 🔧 **Configuration Options**

All standardized tools support these common CLI arguments:

| Argument | Description | Default |
|----------|-------------|---------|
| `--query` | Search query (required) | - |
| `--max-items` | Maximum items to collect | 10 |
| `--analysis-depth` | Analysis level: basic/standard/comprehensive | standard |
| `--frequency` | Research frequency: daily/weekly/biweekly/monthly | daily |
| `--workspace-id` | Workspace identifier | test workspace |
| `--user-id` | User identifier | test user |
| `--config` | Path to JSON config file | - |
| `--daemon` | Run as daemon process | false |
| `--output` | Output file path | stdout |

## 📊 **Custom Parameters**

Each tool supports custom parameters via the `--config` JSON file:

### **Reddit Custom Parameters**
```json
{
  "custom_parameters": {
    "subreddits": ["artificial", "MachineLearning", "productivity"],
    "max_comments_per_post": 10
  }
}
```

### **GitHub Custom Parameters**
```json
{
  "custom_parameters": {
    "include_readme": true,
    "include_issues": true,
    "sort_by": "stars"
  }
}
```

### **Hacker News Custom Parameters**
```json
{
  "custom_parameters": {
    "story_types": ["top", "new", "ask"],
    "max_comments_per_story": 8
  }
}
```

### **Google Trends Custom Parameters**
```json
{
  "custom_parameters": {
    "keywords": ["AI", "machine learning", "automation"],
    "timeframe": "today 12-m",
    "country": "united_states",
    "include_related": true,
    "include_trending": true
  }
}
```

## 🏗️ **Architecture**

### **Base Template**
All tools inherit from `StandardizedResearchTool` which provides:

- **Database Management**: Async Supabase/PostgreSQL operations
- **AI Analysis**: Pydantic AI agent integration
- **Configuration**: Standardized config handling
- **Logging**: Structured logging with context
- **Error Handling**: Consistent error patterns

### **Tool-Specific Implementation**
Each tool implements:

- `collect_raw_data()`: Source-specific data collection
- `_analyze_*_data()`: Enhanced AI analysis for the source
- `_generate_summary()`: Statistical summaries
- `_save_local_results()`: Local file storage

## 🔄 **Data Flow**

1. **Initialize**: Setup database, API clients, logging
2. **Collect**: Gather raw data from source APIs
3. **Analyze**: Process with Pydantic AI agents
4. **Store**: Save to Supabase database
5. **Export**: Save to local JSON files
6. **Cleanup**: Close connections and resources

## 📈 **Output Format**

All tools produce consistent `ResearchResult` objects:

```json
{
  "id": "unique_result_id",
  "source": "reddit|github|hackernews|google_trends",
  "query": "search query",
  "raw_data": { /* source-specific raw data */ },
  "analyzed_data": { /* AI analysis results */ },
  "metadata": { /* tool configuration and stats */ },
  "created_at": "2025-01-16T10:30:00Z",
  "workspace_id": "workspace_uuid",
  "user_id": "user_uuid"
}
```

## 🔍 **Database Schema**

Results are stored in the `research_results` table:

```sql
CREATE TABLE research_results (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  query TEXT NOT NULL,
  raw_data JSONB NOT NULL,
  analyzed_data JSONB,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  workspace_id UUID NOT NULL,
  user_id UUID NOT NULL
);
```

## 🧪 **Testing**

To test a standardized tool:

```bash
# Test Reddit tool
cd social-media-module/backend
python features/reddit_research/cli_reddit_standardized.py \
  --query "test query" \
  --max-items 2 \
  --analysis-depth basic

# Test GitHub tool
python features/github_research/cli_github_standardized.py \
  --query "python" \
  --max-items 3 \
  --analysis-depth basic
```

## 📦 **Dependencies**

Ensure these packages are installed:

```bash
pip install pydantic-ai==0.3.2
pip install pydantic==2.11.7
pip install fastapi==0.115.13
pip install uvicorn==0.34.3
pip install sse-starlette==2.3.6
pip install supabase
pip install asyncpg==0.30.0
pip install python-dotenv==1.1.0
pip install structlog
pip install requests
pip install pytrends  # For Google Trends only
```

## 🔄 **Migration from Original Tools**

Original tools have been preserved in `features/archive/` and can be restored if needed:

```bash
# To restore an original tool (if needed)
cp features/archive/reddit_research/cli_reddit_scraper_simple.py \
   features/reddit_research/
```

## 🎯 **Benefits of Standardization**

- **Consistency**: All tools follow the same patterns
- **Maintainability**: Easier to update and debug
- **Scalability**: Built for production workloads
- **Integration**: Seamless database and API integration
- **Monitoring**: Structured logging and error tracking
- **Compliance**: Follows Project Server Standards v1.0

## 🚨 **Important Notes**

1. **Environment Variables**: Ensure all required env vars are set
2. **Database**: Supabase connection must be configured
3. **API Keys**: Some tools require API tokens (GitHub, etc.)
4. **Dependencies**: Install all required packages
5. **Python Version**: Requires Python 3.11+

## 📞 **Support**

For issues with standardized tools:

1. Check environment variables and dependencies
2. Review logs for specific error messages
3. Test with basic analysis depth first
4. Verify database connectivity
5. Check API rate limits and authentication
