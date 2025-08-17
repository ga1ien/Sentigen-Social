# Reddit API Integration Documentation

## Overview

The Reddit API Worker provides comprehensive content research capabilities using Reddit's official API. This integration enables real-time access to trending content, discussions, and social media intelligence from one of the world's largest social platforms.

## Features

### Core Capabilities
- **Trending Content Research**: Access hot, new, rising, and top posts from any subreddit
- **Content Search**: Search for specific topics across Reddit with advanced filtering
- **Subreddit Analysis**: Get detailed information about communities and their characteristics
- **User Content History**: Analyze posting patterns and content from specific users
- **Trend Analysis**: Comprehensive analysis of content trends, engagement patterns, and popular topics
- **Comment Intelligence**: Optional deep-dive into post discussions and community sentiment

### Authentication & Security
- OAuth2 client credentials flow for secure API access
- Automatic token management and refresh
- Rate limiting compliance with Reddit's API guidelines
- Secure credential handling with environment variable configuration

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Reddit API Credentials
REDDIT_CLIENT_ID=7dj-umFWDSZvyE9LDj9vyA
REDDIT_CLIENT_SECRET=eWfyYnYy3ZLJDZf5UMJpGtorWmLlMg
REDDIT_USER_AGENT=ContentResearch/1.0 by SentigenSocial
```

### API Credentials Setup

1. **Reddit App Registration**: The provided credentials are for the "Content Research" app
   - App Name: Content Research
   - App ID: 7dj-umFWDSZvyE9LDj9vyA
   - App Type: Script/Personal Use Script

2. **User Agent**: Required by Reddit API for identification and rate limiting
   - Format: `AppName/Version by Username`
   - Current: `ContentResearch/1.0 by SentigenSocial`

## Usage Examples

### Basic Usage

```python
from workers.reddit_worker import RedditWorker

# Initialize worker
reddit_worker = RedditWorker()

# Check health
is_healthy = await reddit_worker.health_check()
print(f"Reddit worker healthy: {is_healthy}")
```

### Trending Content Research

```python
# Get trending posts from a specific subreddit
trending_data = await reddit_worker.get_trending_content(
    subreddit="technology",
    time_filter="day",
    limit=25
)

print(f"Found {trending_data['total_posts']} trending posts")
for post in trending_data['posts'][:5]:
    print(f"- {post['title']} (Score: {post['score']})")
```

### Content Search

```python
# Search for specific topics
search_results = await reddit_worker.search_reddit_content(
    query="artificial intelligence",
    subreddit="MachineLearning",
    time_filter="week",
    limit=20
)

print(f"Found {search_results['total_posts']} posts about AI")
```

### Subreddit Analysis

```python
# Analyze trends in a subreddit
trend_analysis = await reddit_worker.analyze_subreddit_trends(
    subreddit="socialmedia",
    time_filter="month",
    limit=100
)

analysis = trend_analysis['analysis']
print(f"Average engagement: {analysis['average_score']} upvotes")
print(f"Top domains: {analysis['top_domains'][:3]}")
```

### User Content Research

```python
# Research a user's posting history
user_content = await reddit_worker.get_user_content_history(
    username="example_user",
    sort_by="top",
    limit=50
)

print(f"User has {user_content['total_posts']} posts")
```

## Task Types

### 1. Trending Posts (`trending_posts`)

Retrieves popular content from subreddits based on various sorting criteria.

**Parameters:**
- `subreddit`: Target subreddit (default: "all")
- `sort_by`: Sorting method - "hot", "new", "rising", "top"
- `time_filter`: Time range for "top" posts - "hour", "day", "week", "month", "year", "all"
- `limit`: Number of posts to retrieve (max: 100)
- `include_comments`: Whether to fetch top comments for each post

**Response Structure:**
```json
{
  "subreddit": "technology",
  "sort_by": "hot",
  "time_filter": "day",
  "posts": [
    {
      "id": "post_id",
      "title": "Post Title",
      "author": "username",
      "subreddit": "technology",
      "score": 1250,
      "upvote_ratio": 0.95,
      "num_comments": 89,
      "created_utc": 1703123456,
      "url": "https://example.com/article",
      "permalink": "https://reddit.com/r/technology/comments/...",
      "selftext": "Post content...",
      "is_video": false,
      "domain": "example.com",
      "flair_text": "News",
      "gilded": 2,
      "awards": 5,
      "over_18": false,
      "top_comments": [...]
    }
  ],
  "total_posts": 25
}
```

### 2. Search Posts (`search_posts`)

Searches for content matching specific queries within subreddits.

**Parameters:**
- `search_query`: Search terms (required)
- `subreddit`: Target subreddit to search within
- `sort_by`: Result sorting - "relevance", "hot", "top", "new", "comments"
- `time_filter`: Time range filter
- `limit`: Maximum results
- `include_comments`: Include top comments

### 3. Subreddit Info (`subreddit_info`)

Retrieves detailed information about a subreddit community.

**Response Structure:**
```json
{
  "name": "technology",
  "title": "Technology",
  "description": "Subreddit dedicated to technology news...",
  "subscribers": 14500000,
  "active_users": 25000,
  "created_utc": 1201242000,
  "over_18": false,
  "lang": "en",
  "subreddit_type": "public",
  "url": "https://reddit.com/r/technology"
}
```

### 4. User Posts (`user_posts`)

Fetches posting history from specific Reddit users.

**Parameters:**
- `username`: Reddit username (required)
- `sort_by`: Sorting method - "new", "hot", "top"
- `limit`: Number of posts to retrieve

### 5. Content Analysis (`content_analysis`)

Provides comprehensive trend analysis for subreddit content.

**Response Structure:**
```json
{
  "subreddit": "technology",
  "time_filter": "week",
  "analysis": {
    "total_posts": 100,
    "total_score": 125000,
    "total_comments": 8500,
    "average_score": 1250.0,
    "average_comments": 85.0,
    "top_domains": [
      ["techcrunch.com", 15],
      ["arstechnica.com", 12],
      ["self.technology", 25]
    ],
    "top_flairs": [
      ["News", 45],
      ["Discussion", 30],
      ["Question", 15]
    ],
    "most_engaging_posts": [
      {
        "title": "Major AI Breakthrough Announced",
        "score": 5000,
        "comments": 450,
        "url": "https://reddit.com/r/technology/comments/..."
      }
    ]
  },
  "posts": [...]
}
```

## Advanced Features

### Comment Analysis

When `include_comments` is enabled, the worker fetches top comments for each post:

```json
{
  "top_comments": [
    {
      "id": "comment_id",
      "author": "commenter",
      "body": "This is a great point about...",
      "score": 150,
      "created_utc": 1703123500,
      "gilded": 1,
      "awards": 2
    }
  ]
}
```

### Rate Limiting & Performance

- **API Limits**: Reddit allows 60 requests per minute for OAuth2 apps
- **Batch Processing**: Worker supports concurrent task processing
- **Token Management**: Automatic token refresh prevents authentication failures
- **Error Handling**: Comprehensive error handling with detailed logging

### Content Filtering

The worker automatically filters out:
- Deleted posts and comments
- NSFW content (when `over_18` flag is present)
- Spam and removed content
- Invalid or malformed data

## Integration Patterns

### With Content Intelligence

```python
# Research trending topics for content creation
trending = await reddit_worker.get_trending_content("socialmedia", "day", 20)

# Extract insights for content worker
content_insights = {
    "trending_topics": [post['title'] for post in trending['posts'][:5]],
    "engagement_patterns": {
        "avg_score": sum(p['score'] for p in trending['posts']) / len(trending['posts']),
        "top_domains": trending.get('analysis', {}).get('top_domains', [])
    }
}
```

### With Research Workflow

```python
# Multi-source research combining Reddit with other platforms
async def comprehensive_research(topic: str):
    # Reddit research
    reddit_data = await reddit_worker.search_reddit_content(
        query=topic,
        subreddit="all",
        time_filter="week"
    )

    # Combine with other research sources
    return {
        "reddit_insights": reddit_data,
        "trending_discussions": reddit_data['posts'][:10],
        "community_sentiment": analyze_sentiment(reddit_data['posts'])
    }
```

## Error Handling

### Common Error Scenarios

1. **Authentication Failures**
   - Invalid credentials
   - Expired tokens
   - Rate limit exceeded

2. **API Errors**
   - Subreddit not found
   - User not found
   - Invalid parameters

3. **Network Issues**
   - Connection timeouts
   - Service unavailable
   - Rate limiting

### Error Response Format

```json
{
  "task_id": "task_123",
  "worker_type": "reddit_worker",
  "status": "error",
  "result": null,
  "error_message": "Detailed error description",
  "execution_time": 2.5
}
```

## Monitoring & Logging

### Health Checks

The worker provides comprehensive health monitoring:

```python
status = reddit_worker.get_status()
print(f"Worker: {status['worker_name']}")
print(f"Healthy: {status['is_healthy']}")
print(f"Last Check: {status['last_health_check']}")
```

### Logging

Structured logging provides detailed insights:

- Task execution times
- API response metrics
- Error details and context
- Rate limiting status
- Authentication events

### Metrics Tracked

- **Request Success Rate**: Percentage of successful API calls
- **Average Response Time**: API call performance metrics
- **Content Volume**: Posts and comments processed
- **Error Rates**: Categorized error tracking
- **Token Usage**: Authentication token lifecycle

## Best Practices

### Performance Optimization

1. **Batch Processing**: Use `batch_process()` for multiple tasks
2. **Appropriate Limits**: Don't request more data than needed
3. **Time Filters**: Use specific time ranges to reduce data volume
4. **Subreddit Targeting**: Focus on relevant communities

### Content Strategy

1. **Trend Identification**: Monitor multiple subreddits for emerging topics
2. **Engagement Analysis**: Focus on high-scoring, well-commented posts
3. **Community Insights**: Understand subreddit culture and preferences
4. **Content Timing**: Analyze posting patterns for optimal timing

### Rate Limit Management

1. **Respect Limits**: Stay within 60 requests per minute
2. **Implement Backoff**: Handle rate limit responses gracefully
3. **Token Lifecycle**: Monitor token expiration and refresh
4. **Request Prioritization**: Focus on high-value data first

## Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Check credentials
echo $REDDIT_CLIENT_ID
echo $REDDIT_CLIENT_SECRET

# Verify user agent format
echo $REDDIT_USER_AGENT
```

**Rate Limiting**
- Monitor request frequency
- Implement exponential backoff
- Use batch processing for efficiency

**Data Quality**
- Filter deleted/removed content
- Handle missing fields gracefully
- Validate data before processing

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import structlog
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = structlog.get_logger(__name__)
```

## API Reference

### RedditWorker Class

#### Methods

- `__init__(config: Optional[Dict[str, Any]] = None)`
- `process_task(task: WorkerTask) -> WorkerResult`
- `health_check() -> bool`
- `get_trending_content(subreddit, time_filter, limit) -> Dict`
- `search_reddit_content(query, subreddit, time_filter, limit) -> Dict`
- `analyze_subreddit_trends(subreddit, time_filter, limit) -> Dict`
- `get_user_content_history(username, sort_by, limit) -> Dict`

#### Configuration Options

- `client_id`: Reddit app client ID
- `client_secret`: Reddit app client secret
- `user_agent`: User agent string for API requests
- `base_url`: Reddit API base URL
- `oauth_url`: OAuth2 token endpoint

## Security Considerations

### Credential Management

- Store credentials in environment variables
- Never commit credentials to version control
- Use secure credential management systems in production
- Rotate credentials periodically

### Data Privacy

- Respect user privacy and Reddit's terms of service
- Don't store personal information unnecessarily
- Implement data retention policies
- Handle NSFW content appropriately

### Rate Limiting Compliance

- Respect Reddit's API rate limits
- Implement proper backoff strategies
- Monitor usage patterns
- Use caching where appropriate

## Future Enhancements

### Planned Features

1. **Real-time Streaming**: WebSocket integration for live updates
2. **Advanced Analytics**: Sentiment analysis and trend prediction
3. **Content Categorization**: Automatic topic classification
4. **User Behavior Analysis**: Posting pattern insights
5. **Cross-platform Integration**: Correlation with other social platforms

### Performance Improvements

1. **Caching Layer**: Redis integration for frequently accessed data
2. **Parallel Processing**: Enhanced concurrent request handling
3. **Data Compression**: Optimized data storage and transfer
4. **Smart Filtering**: AI-powered content relevance scoring

## Support & Resources

### Documentation
- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [OAuth2 Flow Guide](https://github.com/reddit-archive/reddit/wiki/OAuth2)
- [Rate Limiting Guidelines](https://github.com/reddit-archive/reddit/wiki/API)

### Community
- Reddit API Subreddit: r/redditdev
- Official Reddit API Support
- Community-driven examples and tools

### Monitoring
- Built-in health checks and status reporting
- Structured logging for debugging
- Performance metrics and analytics
- Error tracking and alerting
