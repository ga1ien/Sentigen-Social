"""
Content Research and Suggestions API
Provides platform-specific insights and content suggestions
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.openai_client import OpenAIClient
from core.user_auth import get_current_user
from database.supabase_client import get_supabase_client
from utils.ayrshare_client import AyrshareClient

router = APIRouter(prefix="/api/research", tags=["research"])


class PlatformResearchRequest(BaseModel):
    platform: str  # linkedin, twitter, instagram, tiktok, youtube
    topic: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None


class ContentSuggestion(BaseModel):
    platform: str
    title: str
    content: str
    hashtags: List[str]
    best_time_to_post: str
    content_type: str  # text, image, video, carousel
    estimated_engagement: str
    tips: List[str]


class PlatformInsights(BaseModel):
    platform: str
    trending_topics: List[Dict[str, Any]]
    best_practices: List[str]
    optimal_posting_times: List[str]
    recommended_hashtags: List[str]
    content_ideas: List[ContentSuggestion]


@router.post("/platform-insights", response_model=PlatformInsights)
async def get_platform_insights(request: PlatformResearchRequest, current_user: dict = Depends(get_current_user)):
    """Get research insights and suggestions for a specific platform"""
    try:
        openai_client = OpenAIClient()
        db_client = get_supabase_client()

        # Platform-specific content guidelines
        platform_guidelines = {
            "linkedin": {
                "tone": "professional, thought-leadership",
                "length": "1300-2000 characters optimal",
                "format": "long-form posts, articles, polls",
                "best_times": ["Tuesday-Thursday 8-10am", "Tuesday-Wednesday 5-6pm"],
                "hashtag_count": "3-5 hashtags",
            },
            "twitter": {
                "tone": "conversational, concise, witty",
                "length": "100-280 characters",
                "format": "threads, quick updates, retweets with commentary",
                "best_times": ["Weekdays 8-10am", "Weekdays 7-9pm"],
                "hashtag_count": "1-2 hashtags",
            },
            "instagram": {
                "tone": "visual, authentic, lifestyle",
                "length": "138-150 characters for optimal engagement",
                "format": "photos, reels, stories, carousels",
                "best_times": ["Weekdays 11am-1pm", "Weekdays 7-9pm"],
                "hashtag_count": "8-15 hashtags",
            },
            "tiktok": {
                "tone": "entertaining, trendy, authentic",
                "length": "short-form video 15-60 seconds",
                "format": "vertical videos, trends, challenges",
                "best_times": ["6-10am", "7-11pm"],
                "hashtag_count": "3-5 trending hashtags",
            },
            "youtube": {
                "tone": "educational, entertaining, detailed",
                "length": "8-12 minutes optimal",
                "format": "tutorials, vlogs, shorts, long-form",
                "best_times": ["Thursday-Friday 2-4pm"],
                "hashtag_count": "10-15 tags in description",
            },
        }

        guidelines = platform_guidelines.get(request.platform.lower(), {})

        # Generate AI-powered content suggestions
        prompt = f"""
        Generate content research and suggestions for {request.platform}.
        Topic: {request.topic or 'general business content'}
        Industry: {request.industry or 'general'}
        Target Audience: {request.target_audience or 'general audience'}

        Platform Guidelines:
        {json.dumps(guidelines, indent=2)}

        Provide:
        1. Three trending topics relevant to this platform and industry
        2. Five content ideas with full posts/descriptions
        3. Relevant hashtags for each idea
        4. Engagement tips specific to {request.platform}

        Format as JSON with clear structure.
        """

        ai_response = await openai_client.generate_completion(prompt=prompt, max_tokens=2000, temperature=0.7)

        # Parse AI response
        try:
            ai_data = json.loads(ai_response)
        except:
            # Fallback structure if AI response isn't valid JSON
            ai_data = {
                "trending_topics": [
                    {"topic": "AI automation", "relevance": "high"},
                    {"topic": "Sustainability", "relevance": "medium"},
                    {"topic": "Remote work", "relevance": "high"},
                ],
                "content_ideas": [],
            }

        # Build content suggestions
        content_ideas = []
        for i in range(3):
            suggestion = ContentSuggestion(
                platform=request.platform,
                title=f"Content idea {i+1} for {request.platform}",
                content=ai_data.get("content_ideas", [{}])[i].get("content", ""),
                hashtags=ai_data.get("content_ideas", [{}])[i].get("hashtags", []),
                best_time_to_post=guidelines.get("best_times", [""])[0] if guidelines else "",
                content_type="text" if request.platform == "twitter" else "mixed",
                estimated_engagement="High" if i == 0 else "Medium",
                tips=guidelines.get("tips", []),
            )
            content_ideas.append(suggestion)

        # Store insights in database for future reference
        await db_client.service_client.table("ai_suggestions").insert(
            {
                "user_id": current_user["id"],
                "type": f"{request.platform}_insights",
                "title": f"{request.platform.title()} Content Research",
                "description": json.dumps(ai_data),
                "metadata": {
                    "platform": request.platform,
                    "topic": request.topic,
                    "generated_at": datetime.now().isoformat(),
                },
            }
        ).execute()

        return PlatformInsights(
            platform=request.platform,
            trending_topics=ai_data.get("trending_topics", []),
            best_practices=guidelines.get("tips", []),
            optimal_posting_times=guidelines.get("best_times", []),
            recommended_hashtags=ai_data.get("hashtags", []),
            content_ideas=content_ideas,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft-content")
async def draft_platform_content(
    platform: str,
    topic: str,
    tone: Optional[str] = None,
    length: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Generate a draft for specific platform"""
    try:
        openai_client = OpenAIClient()

        platform_prompts = {
            "linkedin": f"""
            Create a LinkedIn post about {topic}.
            Tone: {tone or 'professional, thought-leadership'}
            Length: 1500 characters
            Include:
            - Compelling hook
            - Value-driven content
            - Call to action
            - 3-5 relevant hashtags
            """,
            "twitter": f"""
            Create a Twitter thread about {topic}.
            Tone: {tone or 'conversational, engaging'}
            Format: 5-7 tweets
            Include:
            - Strong opening tweet
            - Numbered thread
            - 1-2 hashtags per tweet
            - Thread recap at end
            """,
            "instagram": f"""
            Create an Instagram caption about {topic}.
            Tone: {tone or 'authentic, visual'}
            Length: 150 characters + expanded caption
            Include:
            - Attention-grabbing first line
            - Story or value
            - Call to action
            - 10-15 relevant hashtags
            """,
            "tiktok": f"""
            Create a TikTok video script about {topic}.
            Tone: {tone or 'entertaining, trendy'}
            Length: 30-60 second script
            Include:
            - Hook (first 3 seconds)
            - Main content
            - Call to action
            - 3-5 trending hashtags
            """,
            "youtube": f"""
            Create a YouTube video outline about {topic}.
            Tone: {tone or 'educational, engaging'}
            Length: 8-10 minute video
            Include:
            - Compelling title
            - Introduction hook
            - Main content sections
            - Call to action
            - Description with keywords
            """,
        }

        prompt = platform_prompts.get(platform.lower(), f"Create content about {topic}")

        content = await openai_client.generate_completion(prompt=prompt, max_tokens=1000, temperature=0.7)

        # Store draft in database
        db_client = get_supabase_client()
        result = (
            await db_client.service_client.table("content_drafts")
            .insert(
                {
                    "user_id": current_user["id"],
                    "platform": platform,
                    "topic": topic,
                    "content": content,
                    "status": "draft",
                    "created_at": datetime.now().isoformat(),
                }
            )
            .execute()
        )

        return {
            "platform": platform,
            "topic": topic,
            "content": content,
            "draft_id": result.data[0]["id"] if result.data else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending-now")
async def get_trending_topics(platforms: Optional[List[str]] = None, current_user: dict = Depends(get_current_user)):
    """Get current trending topics across platforms"""
    try:
        # This could integrate with real trending APIs
        # For now, return curated trending topics
        trending = {
            "linkedin": [
                "AI in business",
                "Sustainable practices",
                "Future of work",
                "Leadership insights",
                "Tech innovations",
            ],
            "twitter": ["Breaking tech news", "Viral memes", "Industry updates", "Quick tips", "Thread topics"],
            "instagram": [
                "Behind the scenes",
                "User generated content",
                "Product showcases",
                "Lifestyle content",
                "Reels trends",
            ],
            "tiktok": ["Trending sounds", "Challenge ideas", "Educational content", "Comedy skits", "How-to videos"],
            "youtube": ["Tutorial series", "Product reviews", "Vlogs", "Shorts ideas", "Long-form content"],
        }

        if platforms:
            filtered_trending = {p: trending.get(p, []) for p in platforms}
            return filtered_trending

        return trending

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule-content")
async def schedule_content_with_ayrshare(
    platform: str,
    content: str,
    scheduled_time: datetime,
    media_urls: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user),
):
    """Schedule content using Ayrshare API"""
    try:
        ayrshare_client = AyrshareClient()

        # Prepare the post data for Ayrshare
        post_data = {"post": content, "platforms": [platform], "scheduleDate": scheduled_time.isoformat()}

        if media_urls:
            post_data["mediaUrls"] = media_urls

        # Send to Ayrshare
        result = await ayrshare_client.create_post(post_data)

        # Store in our database
        db_client = get_supabase_client()
        await db_client.service_client.table("scheduled_posts").insert(
            {
                "user_id": current_user["id"],
                "platform": platform,
                "content": content,
                "scheduled_time": scheduled_time.isoformat(),
                "ayrshare_id": result.get("id"),
                "status": "scheduled",
            }
        ).execute()

        return {
            "success": True,
            "message": f"Content scheduled for {platform} at {scheduled_time}",
            "ayrshare_id": result.get("id"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SaveDraftRequest(BaseModel):
    platform: Optional[str] = None
    title: Optional[str] = None
    content: str


class SaveDraftResponse(BaseModel):
    id: str
    created_at: str


@router.post("/save-draft", response_model=SaveDraftResponse)
async def save_draft(
    request: SaveDraftRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save a user's edited draft to content_drafts."""
    try:
        db_client = get_supabase_client()
        insert_data = {
            "user_id": current_user["id"],
            "platform": request.platform,
            "title": request.title,
            "content": request.content,
            "status": "draft",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        result = db_client.client.table("content_drafts").insert(insert_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save draft")
        row = result.data[0]
        return SaveDraftResponse(id=row.get("id"), created_at=row.get("created_at"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
