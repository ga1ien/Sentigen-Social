"""
UX-focused API endpoints for Research-to-Video workflow
Provides step-by-step control for the frontend interface
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/research-video", tags=["Research Video UX"])


# Request Models
class ResearchSetupRequest(BaseModel):
    """Request to start research phase"""

    research_topics: List[str] = Field(..., min_items=1, max_items=5)
    platforms_to_research: List[str] = Field(default=["reddit", "twitter", "linkedin"])
    target_audience: str = Field(..., min_length=1)
    video_style: str = Field(default="professional")
    max_video_duration: int = Field(default=60, ge=15, le=180)
    research_depth: str = Field(default="comprehensive")


class ScriptGenerationRequest(BaseModel):
    """Request to generate script from research"""

    research_data: Dict[str, Any]
    target_audience: str
    video_style: str
    max_duration: int = 60


class VideoGenerationRequest(BaseModel):
    """Request to generate video from script"""

    script_id: str
    avatar_id: str
    video_style: str


class PublishRequest(BaseModel):
    """Request to publish video to platforms"""

    video_id: str
    platforms: List[str] = Field(default=["tiktok", "instagram_reels", "youtube_shorts"])
    hashtags: Optional[List[str]] = None


# Response Models
class ResearchStatusResponse(BaseModel):
    """Research status response"""

    workflow_id: str
    status: str
    progress: float
    current_step: str
    research_data: Optional[Dict[str, Any]] = None


class ScriptResponse(BaseModel):
    """Script generation response"""

    id: str
    script: str
    quality_score: float
    target_duration: int
    status: str


class VideoResponse(BaseModel):
    """Video generation response"""

    id: str
    status: str
    avatar_id: str
    duration: int
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class PublishResponse(BaseModel):
    """Publishing response"""

    success: bool
    platforms: Dict[str, Any]
    message: str


# Global state for demo (in production, use database)
research_sessions = {}
script_generations = {}
video_generations = {}


@router.post("/start", response_model=Dict[str, Any])
async def start_research_workflow(request: ResearchSetupRequest, background_tasks: BackgroundTasks):
    """Start the research phase of the workflow"""
    try:
        workflow_id = f"workflow_{len(research_sessions) + 1}"

        # Store research session
        research_sessions[workflow_id] = {
            "status": "researching",
            "progress": 0.0,
            "current_step": "Initializing research...",
            "config": request.dict(),
            "created_at": datetime.utcnow(),
        }

        # Start background research task
        background_tasks.add_task(simulate_research, workflow_id, request)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Research started successfully",
            "estimated_completion_time": "2-5 minutes",
        }

    except Exception as e:
        logger.error("Failed to start research", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")


@router.get("/status/{workflow_id}", response_model=ResearchStatusResponse)
async def get_research_status(workflow_id: str):
    """Get the current status of research workflow"""
    try:
        if workflow_id not in research_sessions:
            raise HTTPException(status_code=404, detail="Workflow not found")

        session = research_sessions[workflow_id]

        return ResearchStatusResponse(
            workflow_id=workflow_id,
            status=session["status"],
            progress=session["progress"],
            current_step=session["current_step"],
            research_data=session.get("research_data"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get research status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/generate-script", response_model=ScriptResponse)
async def generate_script_from_research(request: ScriptGenerationRequest):
    """Generate script from research data"""
    try:
        research_data = request.research_data
        target_audience = request.target_audience
        video_style = request.video_style
        max_duration = request.max_duration

        # Generate script based on research
        trending_topics = research_data.get("trending_topics", ["AI automation", "productivity"])
        insights_count = len(research_data.get("insights", []))

        script_content = f"""
🔥 Breaking: {trending_topics[0].title()} is EXPLODING right now!

I just analyzed {insights_count} discussions across Reddit, Twitter, and LinkedIn, and here's what {target_audience} need to know:

✨ Key Insight #1: The conversation is shifting toward practical applications
📈 Key Insight #2: Engagement is 3x higher on {video_style} content
🚀 Key Insight #3: Early adopters are seeing massive results

But here's the thing most people are missing...

The real opportunity isn't just following trends - it's understanding WHY they're trending.

{trending_topics[1] if len(trending_topics) > 1 else 'Smart automation'} is the secret sauce that's separating winners from everyone else.

Want to stay ahead? Here's my prediction for what's coming next...

Drop a 🔥 if this resonates with you!

#TrendingNow #{trending_topics[0].replace(' ', '')} #ContentStrategy
        """.strip()

        script_id = f"script_{hash(script_content) % 10000}"

        # Store script
        script_generations[script_id] = {
            "id": script_id,
            "script": script_content,
            "quality_score": 8.7,
            "target_duration": max_duration,
            "status": "completed",
            "created_at": datetime.utcnow(),
        }

        return ScriptResponse(**script_generations[script_id])

    except Exception as e:
        logger.error("Failed to generate script", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate script: {str(e)}")


@router.post("/generate-video", response_model=VideoResponse)
async def generate_video_from_script(request: VideoGenerationRequest):
    """Generate video from approved script"""
    try:
        script_id = request.script_id
        avatar_id = request.avatar_id
        video_style = request.video_style

        if script_id not in script_generations:
            raise HTTPException(status_code=404, detail="Script not found")

        video_id = f"video_{script_id}_{avatar_id}"

        # Mock video generation (in production, would call HeyGen API)
        video_data = {
            "id": video_id,
            "status": "completed",  # Mock as completed for demo
            "avatar_id": avatar_id,
            "duration": 47,
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "thumbnail_url": "https://via.placeholder.com/640x360/1a1a1a/ffffff?text=AI+Generated+Video",
        }

        # Store video generation
        video_generations[video_id] = video_data

        return VideoResponse(**video_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate video", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")


@router.post("/publish", response_model=PublishResponse)
async def publish_video_to_platforms(request: PublishRequest):
    """Publish approved video to social platforms"""
    try:
        video_id = request.video_id
        platforms = request.platforms
        hashtags = request.hashtags or []

        if video_id not in video_generations:
            raise HTTPException(status_code=404, detail="Video not found")

        # Mock publishing to each platform
        publish_results = {}

        for platform in platforms:
            if platform == "tiktok":
                publish_results[platform] = {
                    "status": "published",
                    "post_id": f"tiktok_{video_id}_{len(publish_results)}",
                    "url": f"https://tiktok.com/@yourhandle/video/{video_id}",
                    "engagement": {"views": 1247, "likes": 89, "shares": 23},
                }
            elif platform == "instagram_reels":
                publish_results[platform] = {
                    "status": "published",
                    "post_id": f"ig_reel_{video_id}_{len(publish_results)}",
                    "url": f"https://instagram.com/reel/{video_id}",
                    "engagement": {"views": 892, "likes": 67, "comments": 12},
                }
            elif platform == "youtube_shorts":
                publish_results[platform] = {
                    "status": "published",
                    "post_id": f"yt_short_{video_id}_{len(publish_results)}",
                    "url": f"https://youtube.com/shorts/{video_id}",
                    "engagement": {"views": 2156, "likes": 134, "subscribers": 8},
                }

        return PublishResponse(
            success=True,
            platforms=publish_results,
            message=f"🎉 Video published successfully to {len(platforms)} platforms!",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to publish video", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to publish video: {str(e)}")


# Background task to simulate research
async def simulate_research(workflow_id: str, request: ResearchSetupRequest):
    """Simulate the research process with realistic timing"""
    try:
        session = research_sessions[workflow_id]

        # Step 1: Initialize
        await asyncio.sleep(2)
        session.update({"progress": 20.0, "current_step": "Scanning Reddit discussions..."})

        # Step 2: Reddit research
        await asyncio.sleep(3)
        session.update({"progress": 40.0, "current_step": "Analyzing Twitter trends..."})

        # Step 3: Twitter research
        await asyncio.sleep(2)
        session.update({"progress": 60.0, "current_step": "Gathering LinkedIn insights..."})

        # Step 4: LinkedIn research
        await asyncio.sleep(2)
        session.update({"progress": 80.0, "current_step": "Processing engagement data..."})

        # Step 5: Final processing
        await asyncio.sleep(1)

        # Generate mock research results
        research_data = {
            "insights": [
                {
                    "platform": "reddit",
                    "content": f"High engagement discussion about {request.research_topics[0]}",
                    "engagement_score": 87,
                    "sentiment": "positive",
                },
                {
                    "platform": "twitter",
                    "content": f"Trending hashtag #{request.research_topics[0].replace(' ', '')}",
                    "engagement_score": 92,
                    "sentiment": "positive",
                },
                {
                    "platform": "linkedin",
                    "content": f"Professional insights on {request.research_topics[0]}",
                    "engagement_score": 78,
                    "sentiment": "neutral",
                },
            ],
            "trending_topics": request.research_topics + ["automation", "productivity", "AI tools"],
            "engagement_data": {
                "average_engagement": 85.7,
                "peak_times": ["9-11 AM", "7-9 PM"],
                "best_platforms": ["twitter", "reddit", "linkedin"],
            },
        }

        session.update(
            {
                "status": "research_completed",
                "progress": 100.0,
                "current_step": "Research complete!",
                "research_data": research_data,
            }
        )

        logger.info("Research simulation completed", workflow_id=workflow_id)

    except Exception as e:
        logger.error("Research simulation failed", error=str(e), workflow_id=workflow_id)
        session.update({"status": "failed", "current_step": f"Research failed: {str(e)}"})
