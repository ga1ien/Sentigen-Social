"""
Chrome MCP Worker for Social Media Intelligence
Leverages Chrome MCP Server for browser automation and content extraction
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

import httpx
import structlog
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from workers.base_worker import BaseWorker, WorkerTask, WorkerResult

logger = structlog.get_logger(__name__)


class Platform(str, Enum):
    """Supported social media platforms"""
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    HACKERNEWS = "hackernews"
    PRODUCTHUNT = "producthunt"
    DEVTO = "dev.to"
    MEDIUM = "medium"
    YOUTUBE = "youtube"


@dataclass
class PlatformConfig:
    """Configuration for each platform"""
    url: str
    selectors: Dict[str, str]
    search_paths: List[str]
    login_required: bool = False
    scroll_strategy: str = "standard"  # "infinite", "pagination"
    rate_limit_delay: float = 2.0  # seconds between requests


# Platform configurations optimized for Chrome MCP
PLATFORM_CONFIGS = {
    Platform.REDDIT: PlatformConfig(
        url="https://reddit.com",
        selectors={
            "post_title": "[data-testid='post-title'], .title a, h3",
            "post_content": "[data-click-id='text'], .usertext-body, .md",
            "upvotes": "[data-testid='upvote'], .score, .upvotes",
            "comments": "[data-testid='comment-tree'], .comments, .comment",
            "subreddit": "[data-testid='subreddit-name'], .subreddit",
            "author": "[data-testid='post-author'], .author"
        },
        search_paths=[
            "/r/artificial",
            "/r/MachineLearning", 
            "/r/LocalLLaMA",
            "/r/singularity",
            "/r/OpenAI",
            "/r/webdev",
            "/r/programming",
            "/r/entrepreneur",
            "/r/marketing"
        ],
        scroll_strategy="infinite",
        rate_limit_delay=1.5
    ),
    Platform.LINKEDIN: PlatformConfig(
        url="https://linkedin.com",
        selectors={
            "post_content": ".feed-shared-text, .feed-shared-update-v2__description",
            "reactions": ".social-counts-reactions, .social-action-bar",
            "comments": ".comments-comments-list, .comment",
            "author": ".feed-shared-actor__name, .update-components-actor__name",
            "company": ".feed-shared-actor__sub-description"
        },
        search_paths=[
            "/feed/",
            "/search/results/content/?keywords=artificial%20intelligence",
            "/search/results/content/?keywords=AI%20automation",
            "/search/results/content/?keywords=machine%20learning",
            "/search/results/content/?keywords=productivity%20tools"
        ],
        login_required=True,
        scroll_strategy="infinite",
        rate_limit_delay=3.0
    ),
    Platform.TWITTER: PlatformConfig(
        url="https://x.com",
        selectors={
            "tweet": "[data-testid='tweet']",
            "tweet_text": "[data-testid='tweetText']",
            "likes": "[data-testid='like']",
            "retweets": "[data-testid='retweet']",
            "replies": "[data-testid='reply']",
            "author": "[data-testid='User-Name']"
        },
        search_paths=[
            "/search?q=AI%20coding&src=typed_query&f=live",
            "/search?q=artificial%20intelligence&src=typed_query&f=live",
            "/search?q=machine%20learning&src=typed_query&f=live",
            "/search?q=automation%20tools&src=typed_query&f=live",
            "/search?q=productivity%20hacks&src=typed_query&f=live"
        ],
        scroll_strategy="infinite",
        rate_limit_delay=2.0
    ),
    Platform.HACKERNEWS: PlatformConfig(
        url="https://news.ycombinator.com",
        selectors={
            "story_title": ".storylink, .titleline > a",
            "score": ".score",
            "comments": ".subtext, .comment",
            "author": ".hnuser"
        },
        search_paths=[
            "/",
            "/best",
            "/newest",
            "/show",
            "/ask"
        ],
        scroll_strategy="pagination",
        rate_limit_delay=1.0
    ),
    Platform.PRODUCTHUNT: PlatformConfig(
        url="https://producthunt.com",
        selectors={
            "product_name": "[data-test='post-name']",
            "description": "[data-test='post-description']",
            "upvotes": "[data-test='vote-button']",
            "comments": "[data-test='comment']"
        },
        search_paths=[
            "/",
            "/topics/artificial-intelligence",
            "/topics/productivity",
            "/topics/developer-tools"
        ],
        scroll_strategy="infinite",
        rate_limit_delay=2.5
    )
}


class ContentInsight(BaseModel):
    """Extracted content insight from social media"""
    platform: Platform
    url: str
    title: str
    content: str
    engagement_score: int
    trending_topics: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    author: Optional[str] = None
    comments_summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self):
        return {
            "platform": self.platform.value,
            "url": self.url,
            "title": self.title,
            "content": self.content[:500],  # Truncate for storage
            "engagement_score": self.engagement_score,
            "trending_topics": self.trending_topics,
            "sentiment": self.sentiment,
            "extracted_at": self.extracted_at.isoformat(),
            "author": self.author,
            "comments_summary": self.comments_summary,
            "metadata": self.metadata
        }


@dataclass
class ChromeWorkerDeps:
    """Dependencies for Chrome MCP worker"""
    platform: Platform
    config: PlatformConfig
    search_query: Optional[str] = None
    date_filter: Optional[str] = None
    max_posts: int = 10
    chrome_mcp_url: str = "http://127.0.0.1:12306/mcp"


class ChromeMCPWorker(BaseWorker):
    """Chrome MCP Worker for social media intelligence"""
    
    def __init__(self):
        super().__init__()
        self.chrome_mcp_url = "http://127.0.0.1:12306/mcp"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.agent = self._create_agent()
        
        logger.info("Chrome MCP Worker initialized")
    
    def _create_agent(self) -> Agent:
        """Create the Chrome automation agent"""
        return Agent(
            model="gpt-4o-mini",
            system_prompt="""
            You are a Chrome automation agent that extracts content insights from social media platforms.
            
            Your tasks:
            1. Navigate to the specified platform using Chrome MCP tools
            2. Search or browse for relevant content
            3. Extract post data including title, content, engagement metrics
            4. Identify trending topics and sentiment from content
            5. Capture valuable insights for content creation
            
            Use Chrome MCP tools efficiently:
            - Navigate to pages with chrome_navigate
            - Extract elements using chrome_get_interactive_elements
            - Get page content with chrome_get_web_content
            - Take screenshots for reference with chrome_screenshot
            - Handle scrolling for infinite scroll pages
            - Search tab content with search_tabs_content
            
            Focus on high-engagement content and emerging trends.
            Be thorough but efficient to avoid rate limiting.
            """,
            deps_type=ChromeWorkerDeps,
            retries=2
        )
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """Process a social media intelligence task"""
        try:
            task_data = task.data
            platform = Platform(task_data.get("platform", "reddit"))
            config = PLATFORM_CONFIGS.get(platform)
            
            if not config:
                raise ValueError(f"Unsupported platform: {platform}")
            
            deps = ChromeWorkerDeps(
                platform=platform,
                config=config,
                search_query=task_data.get("search_query"),
                date_filter=task_data.get("date_filter"),
                max_posts=task_data.get("max_posts", 10),
                chrome_mcp_url=self.chrome_mcp_url
            )
            
            # Run the Chrome automation agent
            prompt = f"""
            Scan {platform.value} for content insights:
            - Platform: {platform.value}
            - Search query: {deps.search_query or 'trending content'}
            - Max posts: {deps.max_posts}
            - Focus on: AI, technology, productivity, automation topics
            
            Extract high-engagement posts with titles, content, engagement metrics, and trending topics.
            """
            
            result = await self.agent.run(prompt, deps=deps)
            
            # Process the results
            insights = await self._extract_insights_from_result(result, platform, config)
            
            return WorkerResult(
                task_id=task.id,
                status="completed",
                result={
                    "insights": [insight.to_dict() for insight in insights],
                    "platform": platform.value,
                    "total_extracted": len(insights),
                    "extraction_time": datetime.utcnow().isoformat()
                },
                metadata={
                    "platform": platform.value,
                    "search_query": deps.search_query,
                    "extraction_method": "chrome_mcp"
                }
            )
            
        except Exception as e:
            logger.error("Chrome MCP task failed", error=str(e), task_id=task.id)
            return WorkerResult(
                task_id=task.id,
                status="failed",
                error=str(e),
                result={}
            )
    
    async def _extract_insights_from_result(
        self, 
        result: Any, 
        platform: Platform, 
        config: PlatformConfig
    ) -> List[ContentInsight]:
        """Extract structured insights from agent result"""
        insights = []
        
        try:
            # Get the raw content from Chrome MCP
            content_data = await self._get_platform_content(platform, config)
            
            # Process each piece of content
            for item in content_data:
                insight = ContentInsight(
                    platform=platform,
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    engagement_score=self._calculate_engagement_score(item),
                    trending_topics=self._extract_trending_topics(item.get("content", "")),
                    sentiment=self._analyze_sentiment(item.get("content", "")),
                    author=item.get("author"),
                    metadata=item.get("metadata", {})
                )
                insights.append(insight)
            
            # Sort by engagement score
            insights.sort(key=lambda x: x.engagement_score, reverse=True)
            
        except Exception as e:
            logger.error("Failed to extract insights", error=str(e))
        
        return insights
    
    async def _get_platform_content(
        self, 
        platform: Platform, 
        config: PlatformConfig
    ) -> List[Dict[str, Any]]:
        """Get content from platform using Chrome MCP"""
        content_items = []
        
        try:
            # Navigate to platform
            await self._chrome_navigate(config.url)
            await asyncio.sleep(2)  # Wait for page load
            
            # For each search path, extract content
            for search_path in config.search_paths[:3]:  # Limit to first 3 paths
                full_url = config.url + search_path
                await self._chrome_navigate(full_url)
                await asyncio.sleep(config.rate_limit_delay)
                
                # Get page content
                page_content = await self._chrome_get_content()
                
                # Extract elements using selectors
                elements = await self._chrome_extract_elements(config.selectors)
                
                # Process elements into content items
                items = self._process_elements_to_content(elements, full_url, platform)
                content_items.extend(items)
                
                # Handle scrolling for infinite scroll platforms
                if config.scroll_strategy == "infinite":
                    await self._handle_infinite_scroll(config)
                
                # Limit total items
                if len(content_items) >= 50:
                    break
            
        except Exception as e:
            logger.error("Failed to get platform content", error=str(e))
        
        return content_items[:20]  # Return top 20 items
    
    async def _chrome_navigate(self, url: str) -> bool:
        """Navigate Chrome to URL using MCP"""
        try:
            response = await self.client.post(
                f"{self.chrome_mcp_url}/tools/chrome_navigate",
                json={"url": url}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Chrome navigate failed", error=str(e))
            return False
    
    async def _chrome_get_content(self) -> str:
        """Get page content using Chrome MCP"""
        try:
            response = await self.client.post(
                f"{self.chrome_mcp_url}/tools/chrome_get_web_content",
                json={}
            )
            if response.status_code == 200:
                return response.json().get("content", "")
        except Exception as e:
            logger.error("Chrome get content failed", error=str(e))
        return ""
    
    async def _chrome_extract_elements(
        self, 
        selectors: Dict[str, str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract elements using Chrome MCP"""
        elements = {}
        
        for element_type, selector in selectors.items():
            try:
                response = await self.client.post(
                    f"{self.chrome_mcp_url}/tools/chrome_get_interactive_elements",
                    json={"selector": selector}
                )
                if response.status_code == 200:
                    elements[element_type] = response.json().get("elements", [])
            except Exception as e:
                logger.error("Element extraction failed", 
                           element_type=element_type, error=str(e))
                elements[element_type] = []
        
        return elements
    
    async def _handle_infinite_scroll(self, config: PlatformConfig):
        """Handle infinite scroll for platforms that support it"""
        try:
            # Scroll down to load more content
            for _ in range(3):  # Scroll 3 times
                await self.client.post(
                    f"{self.chrome_mcp_url}/tools/chrome_keyboard",
                    json={"key": "PageDown"}
                )
                await asyncio.sleep(config.rate_limit_delay)
        except Exception as e:
            logger.error("Infinite scroll failed", error=str(e))
    
    def _process_elements_to_content(
        self, 
        elements: Dict[str, List[Dict[str, Any]]], 
        url: str, 
        platform: Platform
    ) -> List[Dict[str, Any]]:
        """Process extracted elements into content items"""
        content_items = []
        
        # Get the main content elements
        titles = elements.get("post_title", elements.get("story_title", []))
        contents = elements.get("post_content", elements.get("description", []))
        authors = elements.get("author", [])
        
        # Combine elements into content items
        max_items = min(len(titles), 10)  # Limit to 10 items per page
        
        for i in range(max_items):
            try:
                title = titles[i].get("text", "") if i < len(titles) else ""
                content = contents[i].get("text", "") if i < len(contents) else ""
                author = authors[i].get("text", "") if i < len(authors) else ""
                
                if title or content:  # Only add if we have some content
                    content_items.append({
                        "title": title,
                        "content": content,
                        "author": author,
                        "url": url,
                        "platform": platform.value,
                        "metadata": {
                            "extraction_index": i,
                            "element_count": len(titles)
                        }
                    })
            except Exception as e:
                logger.error("Failed to process element", index=i, error=str(e))
                continue
        
        return content_items
    
    def _calculate_engagement_score(self, item: Dict[str, Any]) -> int:
        """Calculate engagement score based on available metrics"""
        score = 0
        
        # Base score from content length and quality
        content_length = len(item.get("content", ""))
        if content_length > 100:
            score += min(content_length // 10, 50)
        
        # Bonus for having author
        if item.get("author"):
            score += 10
        
        # Bonus for title quality
        title = item.get("title", "")
        if len(title) > 20:
            score += 15
        
        # Platform-specific scoring
        platform = item.get("platform", "")
        if platform in ["linkedin", "twitter"]:
            score += 20  # Professional platforms get bonus
        
        return max(score, 1)  # Minimum score of 1
    
    def _extract_trending_topics(self, content: str) -> List[str]:
        """Extract trending topics from content"""
        if not content:
            return []
        
        # Common trending topics in tech/AI space
        trending_keywords = [
            "AI", "artificial intelligence", "machine learning", "automation",
            "productivity", "remote work", "startup", "SaaS", "API",
            "blockchain", "cryptocurrency", "web3", "NFT", "metaverse",
            "cloud computing", "DevOps", "microservices", "kubernetes",
            "react", "python", "javascript", "typescript", "node.js",
            "data science", "analytics", "big data", "IoT", "cybersecurity"
        ]
        
        content_lower = content.lower()
        found_topics = []
        
        for keyword in trending_keywords:
            if keyword.lower() in content_lower:
                found_topics.append(keyword)
        
        return found_topics[:5]  # Return top 5 topics
    
    def _analyze_sentiment(self, content: str) -> str:
        """Simple sentiment analysis"""
        if not content:
            return "neutral"
        
        positive_words = ["great", "awesome", "amazing", "excellent", "love", "best", "fantastic"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "horrible", "disappointing"]
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def health_check(self) -> bool:
        """Check if Chrome MCP server is available"""
        try:
            response = await self.client.get(f"{self.chrome_mcp_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the worker and cleanup resources"""
        await self.client.aclose()
        logger.info("Chrome MCP Worker closed")
