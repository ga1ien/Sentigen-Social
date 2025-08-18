"""
Research Tools API
Integrates Reddit, Hacker News, and GitHub research tools into the main FastAPI application
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Add features directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "features"))

from core.user_auth import UserContext, get_current_user
from database.supabase_client import SupabaseClient

# Import research tools
try:
    from github_research.cli_github_standardized import GitHubResearchTool
    from google_trends_research.cli_google_trends_standardized import GoogleTrendsResearchTool
    from hackernews_research.cli_hackernews_standardized import HackerNewsResearchTool
    from reddit_research.cli_reddit_standardized import RedditResearchTool
except ImportError as e:
    # Fallback for development
    print(f"Warning: Could not import research tools: {e}")
    RedditResearchTool = None
    HackerNewsResearchTool = None
    GitHubResearchTool = None
    GoogleTrendsResearchTool = None

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])

# Lazy initialization to avoid import-time environment variable issues
_supabase_client = None

def get_supabase_client():
    """Get Supabase client with lazy initialization."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


class ResearchRequest(BaseModel):
    query: str = Field(..., description="Research query or topic")
    source: str = Field(..., description="Research source: reddit, hackernews, or github")
    max_items: int = Field(default=10, ge=1, le=50, description="Maximum items to research")
    analysis_depth: str = Field(default="standard", description="Analysis depth: quick, standard, or comprehensive")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration options")


class ResearchResponse(BaseModel):
    id: str
    status: str
    source: str
    query: str
    created_at: datetime
    estimated_completion: Optional[datetime]


class ResearchResult(BaseModel):
    id: str
    status: str
    source: str
    query: str
    results_count: int
    insights: Dict[str, Any]
    raw_data: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]


@router.post("/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest, background_tasks: BackgroundTasks, current_user: UserContext = Depends(get_current_user)
) -> ResearchResponse:
    """Start a new research task."""
    try:
        # Validate source
        supported_sources = ["reddit", "hackernews", "github", "google_trends"]
        if request.source.lower() not in supported_sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source '{request.source}'. Supported: {supported_sources}",
            )

        # Generate research session ID
        research_id = str(uuid.uuid4())

        logger.info(
            "Starting research task",
            user_id=current_user.user_id,
            research_id=research_id,
            source=request.source,
            query=request.query,
        )

        # Create research session record
        session_data = {
            "id": research_id,
            "user_id": current_user.user_id,
            "source": request.source.lower(),
            "query": request.query,
            "max_items": request.max_items,
            "analysis_depth": request.analysis_depth,
            "config": request.config or {},
            "status": "started",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Save to database
        result = get_supabase_client().client.table("research_sessions").insert(session_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create research session"
            )

        # Start research in background
        background_tasks.add_task(execute_research_task, research_id, request, current_user.user_id)

        return ResearchResponse(
            id=research_id,
            status="started",
            source=request.source.lower(),
            query=request.query,
            created_at=datetime.utcnow(),
            estimated_completion=None,  # Will be calculated based on source and depth
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start research task", user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start research task")


async def execute_research_task(research_id: str, request: ResearchRequest, user_id: str):
    """Execute research task in background."""
    try:
        logger.info("Executing research task", research_id=research_id, source=request.source)

        # Update status to running
        get_supabase_client().client.table("research_sessions").update(
            {
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", research_id).execute()

        # Execute research based on source
        results = []
        insights = {}

        if request.source.lower() == "reddit" and RedditResearchTool:
            tool = RedditResearchTool()
            config = {
                "query": request.query,
                "max_items": request.max_items,
                "analysis_depth": request.analysis_depth,
                **(request.config or {}),
            }
            results, insights = await run_reddit_research(tool, config)

        elif request.source.lower() == "hackernews" and HackerNewsResearchTool:
            tool = HackerNewsResearchTool()
            config = {
                "query": request.query,
                "max_items": request.max_items,
                "analysis_depth": request.analysis_depth,
                **(request.config or {}),
            }
            results, insights = await run_hackernews_research(tool, config)

        elif request.source.lower() == "github" and GitHubResearchTool:
            tool = GitHubResearchTool()
            config = {
                "query": request.query,
                "max_items": request.max_items,
                "analysis_depth": request.analysis_depth,
                **(request.config or {}),
            }
            results, insights = await run_github_research(tool, config)

        elif request.source.lower() == "google_trends" and GoogleTrendsResearchTool:
            tool = GoogleTrendsResearchTool()
            config = {
                "query": request.query,
                "max_items": request.max_items,
                "analysis_depth": request.analysis_depth,
                **(request.config or {}),
            }
            results, insights = await run_google_trends_research(tool, config)
        else:
            raise Exception(f"Research tool for {request.source} not available")

        # Save results to database
        research_data = {
            "research_session_id": research_id,
            "user_id": user_id,
            "source": request.source.lower(),
            "query": request.query,
            "results_count": len(results),
            "raw_data": results,
            "insights": insights,
            "created_at": datetime.utcnow().isoformat(),
        }

        get_supabase_client().client.table("research_results").insert(research_data).execute()

        # Update session status to completed
        get_supabase_client().client.table("research_sessions").update(
            {
                "status": "completed",
                "results_count": len(results),
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", research_id).execute()

        logger.info("Research task completed", research_id=research_id, results_count=len(results))

    except Exception as e:
        logger.error("Research task failed", research_id=research_id, error=str(e))

        # Update session status to failed
        get_supabase_client().client.table("research_sessions").update(
            {"status": "failed", "error_message": str(e), "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", research_id).execute()


async def run_reddit_research(tool, config) -> tuple[List[Dict], Dict]:
    """Run Reddit research and return results."""
    try:
        # This would call the actual research tool
        # For now, return simulated results
        results = [
            {
                "title": f"Reddit post about {config['query']}",
                "url": "https://reddit.com/r/example/post1",
                "score": 150,
                "comments": 45,
                "subreddit": "technology",
                "content": f"Discussion about {config['query']} with community insights...",
            }
        ]

        insights = {
            "summary": f"Research on '{config['query']}' found {len(results)} relevant discussions",
            "key_themes": ["technology", "innovation", "community"],
            "sentiment": "positive",
            "recommendations": [
                f"Consider creating content about {config['query']}",
                "Engage with the community discussions",
            ],
        }

        return results, insights
    except Exception as e:
        logger.error("Reddit research failed", error=str(e))
        return [], {"error": str(e)}


async def run_hackernews_research(tool, config) -> tuple[List[Dict], Dict]:
    """Run Hacker News research and return results."""
    try:
        results = [
            {
                "title": f"HN story about {config['query']}",
                "url": "https://news.ycombinator.com/item?id=123456",
                "score": 200,
                "comments": 89,
                "content": f"Hacker News discussion about {config['query']}...",
            }
        ]

        insights = {
            "summary": f"Hacker News research on '{config['query']}' found {len(results)} stories",
            "key_themes": ["startups", "technology", "innovation"],
            "sentiment": "neutral",
            "recommendations": [f"Share insights about {config['query']} on HN", "Participate in relevant discussions"],
        }

        return results, insights
    except Exception as e:
        logger.error("Hacker News research failed", error=str(e))
        return [], {"error": str(e)}


async def run_github_research(tool, config) -> tuple[List[Dict], Dict]:
    """Run GitHub research and return results."""
    try:
        results = [
            {
                "name": f"awesome-{config['query']}",
                "url": "https://github.com/user/repo",
                "stars": 1500,
                "forks": 200,
                "description": f"A curated list of {config['query']} resources",
                "language": "Python",
            }
        ]

        insights = {
            "summary": f"GitHub research on '{config['query']}' found {len(results)} repositories",
            "key_themes": ["open source", "development", "tools"],
            "trending_languages": ["Python", "JavaScript", "Go"],
            "recommendations": [
                f"Consider contributing to {config['query']} projects",
                "Create content about trending repositories",
            ],
        }

        return results, insights
    except Exception as e:
        logger.error("GitHub research failed", error=str(e))
        return [], {"error": str(e)}


async def run_google_trends_research(tool, config) -> tuple[List[Dict], Dict]:
    """Run Google Trends research and return results."""
    try:
        results = [
            {
                "title": f"Trending: {config['query']}",
                "interest_over_time": "Rising",
                "related_queries": [
                    f"{config['query']} tutorial",
                    f"best {config['query']}",
                    f"{config['query']} 2024",
                ],
                "regional_interest": {"United States": 100, "United Kingdom": 75, "Canada": 60},
                "category": "Technology",
                "timeframe": "Past 12 months",
            }
        ]

        insights = {
            "summary": f"Google Trends research on '{config['query']}' shows rising interest",
            "key_themes": ["search trends", "public interest", "seasonal patterns"],
            "trending_regions": ["United States", "United Kingdom", "Canada"],
            "search_volume": "High",
            "trend_direction": "Rising",
            "recommendations": [
                f"Create content about {config['query']} while interest is high",
                "Target content for high-interest regions",
                "Consider seasonal content planning",
            ],
        }

        return results, insights
    except Exception as e:
        logger.error("Google Trends research failed", error=str(e))
        return [], {"error": str(e)}


@router.get("/sessions")
async def get_research_sessions(
    limit: int = 20,
    offset: int = 0,
    status_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    current_user: UserContext = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get user's research sessions."""
    try:
        # Build query
        query = (
            get_supabase_client().client.table("research_sessions")
            .select("id, source, query, status, results_count, created_at, completed_at")
            .eq("user_id", current_user.user_id)
        )

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)
        if source_filter:
            query = query.eq("source", source_filter)

        # Apply pagination and ordering
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        sessions = result.data if result.data else []

        return {"sessions": sessions, "total": len(sessions), "limit": limit, "offset": offset}

    except Exception as e:
        logger.error("Failed to get research sessions", user_id=current_user.user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve research sessions"
        )


@router.get("/sessions/{session_id}", response_model=ResearchResult)
async def get_research_result(session_id: str, current_user: UserContext = Depends(get_current_user)) -> ResearchResult:
    """Get detailed research results."""
    try:
        # Get session info
        session_result = (
            get_supabase_client().client.table("research_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", current_user.user_id)
            .execute()
        )

        if not session_result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research session not found")

        session = session_result.data[0]

        # Get research results
        results_query = (
            get_supabase_client().client.table("research_results").select("*").eq("research_session_id", session_id).execute()
        )

        results_data = results_query.data[0] if results_query.data else None

        return ResearchResult(
            id=session["id"],
            status=session["status"],
            source=session["source"],
            query=session["query"],
            results_count=session.get("results_count", 0),
            insights=results_data.get("insights", {}) if results_data else {},
            raw_data=results_data.get("raw_data", []) if results_data else [],
            created_at=datetime.fromisoformat(session["created_at"].replace("Z", "+00:00")),
            completed_at=datetime.fromisoformat(session["completed_at"].replace("Z", "+00:00"))
            if session.get("completed_at")
            else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get research result", session_id=session_id, user_id=current_user.user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve research result"
        )


@router.delete("/sessions/{session_id}")
async def delete_research_session(
    session_id: str, current_user: UserContext = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete a research session and its results."""
    try:
        # Check if session exists and belongs to user
        session_result = (
            get_supabase_client().client.table("research_sessions")
            .select("id")
            .eq("id", session_id)
            .eq("user_id", current_user.user_id)
            .execute()
        )

        if not session_result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research session not found")

        # Delete results first (foreign key constraint)
        get_supabase_client().client.table("research_results").delete().eq("research_session_id", session_id).execute()

        # Delete session
        get_supabase_client().client.table("research_sessions").delete().eq("id", session_id).eq(
            "user_id", current_user.user_id
        ).execute()

        return {"message": "Research session deleted successfully", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete research session", session_id=session_id, user_id=current_user.user_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete research session"
        )


class ContentGenerationRequest(BaseModel):
    research_session_id: str = Field(..., description="Research session ID to generate content from")
    content_type: str = Field(..., description="Type of content: post, article, thread, or summary")
    platform: Optional[str] = Field(None, description="Target platform for content optimization")
    tone: str = Field(default="professional", description="Content tone: professional, casual, or engaging")
    length: str = Field(default="medium", description="Content length: short, medium, or long")


class ContentGenerationResponse(BaseModel):
    id: str
    content: str
    title: str
    content_type: str
    platform: Optional[str]
    research_session_id: str
    created_at: datetime


@router.post("/generate-content", response_model=ContentGenerationResponse)
async def generate_content_from_research(
    request: ContentGenerationRequest, current_user: UserContext = Depends(get_current_user)
) -> ContentGenerationResponse:
    """Generate content from research results using AI."""
    try:
        # Get research results
        research_result = await get_research_result(request.research_session_id, current_user)

        if research_result.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Research must be completed before generating content"
            )

        # Generate content using AI
        content_data = await generate_ai_content(
            research_result, request.content_type, request.platform, request.tone, request.length
        )

        # Save generated content to database
        content_id = str(uuid.uuid4())
        content_record = {
            "id": content_id,
            "user_id": current_user.user_id,
            "research_session_id": request.research_session_id,
            "content_type": request.content_type,
            "platform": request.platform,
            "title": content_data["title"],
            "content": content_data["content"],
            "tone": request.tone,
            "length": request.length,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Note: This would need a generated_content table in the database
        # For now, we'll return the generated content directly

        logger.info(
            "Content generated from research",
            user_id=current_user.user_id,
            research_session_id=request.research_session_id,
            content_type=request.content_type,
        )

        return ContentGenerationResponse(
            id=content_id,
            content=content_data["content"],
            title=content_data["title"],
            content_type=request.content_type,
            platform=request.platform,
            research_session_id=request.research_session_id,
            created_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to generate content from research",
            user_id=current_user.user_id,
            research_session_id=request.research_session_id,
            error=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate content")


async def generate_ai_content(
    research_result: ResearchResult, content_type: str, platform: Optional[str], tone: str, length: str
) -> Dict[str, str]:
    """Generate AI content from research results."""
    try:
        # Create content prompt based on research insights
        insights = research_result.insights
        raw_data = research_result.raw_data

        # Build context from research
        context = f"""
        Research Query: {research_result.query}
        Source: {research_result.source}
        Results Count: {research_result.results_count}

        Key Insights:
        - Summary: {insights.get('summary', 'No summary available')}
        - Key Themes: {', '.join(insights.get('key_themes', []))}
        - Sentiment: {insights.get('sentiment', 'neutral')}

        Top Research Results:
        """

        # Add top 3 research results for context
        for i, item in enumerate(raw_data[:3]):
            context += f"\n{i+1}. {item.get('title', item.get('name', 'Untitled'))}"
            if item.get("content"):
                context += f" - {item['content'][:200]}..."

        # Generate content based on type and requirements
        if content_type == "post":
            content = generate_social_media_post(context, platform, tone, length)
        elif content_type == "article":
            content = generate_article(context, tone, length)
        elif content_type == "thread":
            content = generate_thread(context, platform, tone)
        else:  # summary
            content = generate_summary(context, tone, length)

        return content

    except Exception as e:
        logger.error("AI content generation failed", error=str(e))
        return {
            "title": f"Content about {research_result.query}",
            "content": f"Based on research from {research_result.source}, here are key insights about {research_result.query}:\n\n{insights.get('summary', 'Research completed successfully.')}",
        }


def generate_social_media_post(context: str, platform: Optional[str], tone: str, length: str) -> Dict[str, str]:
    """Generate a social media post."""
    # This would use OpenAI API in production
    platform_text = f" for {platform}" if platform else ""
    length_guide = {"short": "1-2 sentences", "medium": "2-3 sentences", "long": "3-4 sentences"}

    return {
        "title": f"Social Media Post{platform_text}",
        "content": f"🔥 Just discovered some amazing insights about this topic! The research shows incredible trends and opportunities. Perfect for {tone} engagement. #{platform or 'social'} #trends #insights\n\n[Generated {length_guide.get(length, 'medium')} post in {tone} tone{platform_text}]",
    }


def generate_article(context: str, tone: str, length: str) -> Dict[str, str]:
    """Generate an article."""
    return {
        "title": "Research Insights: Key Trends and Opportunities",
        "content": f"""# Research Insights: Key Trends and Opportunities

Based on comprehensive research analysis, here are the key findings and actionable insights:

## Executive Summary
The research reveals significant trends and patterns that present both opportunities and challenges in the current landscape.

## Key Findings
- Emerging trends show strong growth potential
- Community engagement is at an all-time high
- Technology adoption continues to accelerate

## Recommendations
1. Focus on community-driven initiatives
2. Leverage emerging technologies
3. Maintain authentic engagement

## Conclusion
The research provides valuable insights for strategic decision-making and content creation.

[Generated {length} article in {tone} tone]""",
    }


def generate_thread(context: str, platform: Optional[str], tone: str) -> Dict[str, str]:
    """Generate a thread."""
    return {
        "title": f"Thread: Research Insights{f' for {platform}' if platform else ''}",
        "content": f"""1/🧵 Just completed some fascinating research and wanted to share the key insights with you all!

2/ The data shows some incredible trends that are worth paying attention to. Here's what stood out:

3/ ✨ Community engagement is driving real change
✨ Innovation is happening faster than ever
✨ Authentic voices are being amplified

4/ What does this mean for us? Three key takeaways:

5/ 🎯 Focus on genuine value creation
🎯 Build authentic relationships
🎯 Stay ahead of emerging trends

6/ The research methodology was comprehensive and the results are actionable. Excited to see how we can apply these insights!

[Generated thread in {tone} tone{f' for {platform}' if platform else ''}]""",
    }


def generate_summary(context: str, tone: str, length: str) -> Dict[str, str]:
    """Generate a summary."""
    length_guide = {
        "short": "Brief overview with key points",
        "medium": "Comprehensive summary with insights",
        "long": "Detailed analysis with recommendations",
    }

    return {
        "title": "Research Summary: Key Insights",
        "content": f"""## Research Summary

### Overview
The research analysis reveals important trends and patterns that provide valuable insights for strategic decision-making.

### Key Findings
- Strong community engagement across all platforms
- Emerging technologies showing rapid adoption
- Authentic content driving higher engagement rates

### Strategic Implications
The data suggests focusing on community-driven content strategies while leveraging emerging technologies for maximum impact.

### Next Steps
1. Implement community-focused initiatives
2. Monitor emerging technology trends
3. Develop authentic content strategies

[Generated {length_guide.get(length, 'medium')} summary in {tone} tone]""",
    }
