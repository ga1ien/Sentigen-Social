#!/usr/bin/env python3
"""
Research Configuration API
FastAPI endpoints for managing user research configurations
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from features.reddit_research.research_scheduler import ResearchScheduler
from features.reddit_research.user_research_config import (
    AnalysisDepth,
    ContentSource,
    LinkedInConfig,
    RedditConfig,
    ResearchFrequency,
    ResearchSchedule,
    TwitterConfig,
    UserResearchConfig,
    UserResearchConfigManager,
)

app = FastAPI(title="Research Configuration API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config_manager = UserResearchConfigManager()
scheduler = ResearchScheduler()


# Pydantic models for API requests/responses
class RedditConfigRequest(BaseModel):
    subreddits: List[str] = Field(..., example=["artificial", "productivity"])
    search_topics: List[str] = Field(..., example=["AI automation", "business tools"])
    max_posts_per_subreddit: int = Field(10, ge=1, le=50)
    max_comments_per_post: int = Field(25, ge=5, le=100)
    sort_by: str = Field("hot", regex="^(hot|new|top|rising)$")
    time_filter: str = Field("week", regex="^(hour|day|week|month|year|all)$")
    min_score: int = Field(10, ge=0)
    exclude_nsfw: bool = True
    include_stickied: bool = False


class LinkedInConfigRequest(BaseModel):
    search_topics: List[str] = Field(..., example=["AI automation", "business productivity"])
    company_pages: List[str] = Field(default_factory=list, example=["openai", "microsoft"])
    industry_hashtags: List[str] = Field(default_factory=list, example=["#AI", "#automation"])
    max_posts_per_topic: int = Field(15, ge=1, le=50)
    include_comments: bool = True
    max_comments_per_post: int = Field(20, ge=5, le=100)
    post_types: List[str] = Field(default_factory=lambda: ["article", "video", "image"])


class TwitterConfigRequest(BaseModel):
    search_topics: List[str] = Field(..., example=["AI automation", "startup tools"])
    hashtags: List[str] = Field(default_factory=list, example=["#AI", "#startup"])
    accounts_to_monitor: List[str] = Field(default_factory=list, example=["paulg", "naval"])
    max_tweets_per_topic: int = Field(50, ge=1, le=100)
    include_replies: bool = True
    include_retweets: bool = False
    min_engagement: int = Field(5, ge=0)


class ResearchScheduleRequest(BaseModel):
    frequency: ResearchFrequency
    time_of_day: str = Field("09:00", regex="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = Field("UTC", example="America/New_York")
    days_of_week: Optional[List[int]] = Field(None, example=[0, 2, 4])  # Mon, Wed, Fri
    custom_cron: Optional[str] = None


class UserResearchConfigRequest(BaseModel):
    user_id: str = Field(..., example="user_001")
    workspace_id: str = Field(..., example="workspace_001")
    config_name: str = Field(..., example="ai_business_tools")
    description: str = Field(..., example="Daily research on AI automation tools")

    enabled_sources: List[ContentSource]
    reddit_config: Optional[RedditConfigRequest] = None
    linkedin_config: Optional[LinkedInConfigRequest] = None
    twitter_config: Optional[TwitterConfigRequest] = None

    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    ai_model: str = Field("gpt-5-mini", example="gpt-5-mini")
    focus_areas: List[str] = Field(default_factory=lambda: ["business_intelligence", "trend_analysis"])

    schedule: Optional[ResearchScheduleRequest] = None
    auto_run_enabled: bool = False

    generate_summary: bool = True
    generate_insights: bool = True
    generate_content_ideas: bool = True
    export_formats: List[str] = Field(default_factory=lambda: ["json", "markdown"])


class ConfigUpdateRequest(BaseModel):
    description: Optional[str] = None
    enabled_sources: Optional[List[ContentSource]] = None
    reddit_config: Optional[RedditConfigRequest] = None
    linkedin_config: Optional[LinkedInConfigRequest] = None
    twitter_config: Optional[TwitterConfigRequest] = None
    analysis_depth: Optional[AnalysisDepth] = None
    focus_areas: Optional[List[str]] = None
    schedule: Optional[ResearchScheduleRequest] = None
    auto_run_enabled: Optional[bool] = None
    generate_summary: Optional[bool] = None
    generate_insights: Optional[bool] = None
    generate_content_ideas: Optional[bool] = None
    export_formats: Optional[List[str]] = None


# Helper functions
def convert_request_to_config(request: UserResearchConfigRequest) -> UserResearchConfig:
    """Convert API request to UserResearchConfig dataclass"""

    # Convert nested configs
    reddit_config = None
    if request.reddit_config:
        reddit_config = RedditConfig(**request.reddit_config.dict())

    linkedin_config = None
    if request.linkedin_config:
        linkedin_config = LinkedInConfig(**request.linkedin_config.dict())

    twitter_config = None
    if request.twitter_config:
        twitter_config = TwitterConfig(**request.twitter_config.dict())

    schedule = None
    if request.schedule:
        schedule = ResearchSchedule(**request.schedule.dict())

    return UserResearchConfig(
        user_id=request.user_id,
        workspace_id=request.workspace_id,
        config_name=request.config_name,
        description=request.description,
        enabled_sources=request.enabled_sources,
        reddit_config=reddit_config,
        linkedin_config=linkedin_config,
        twitter_config=twitter_config,
        analysis_depth=request.analysis_depth,
        ai_model=request.ai_model,
        focus_areas=request.focus_areas,
        schedule=schedule,
        auto_run_enabled=request.auto_run_enabled,
        generate_summary=request.generate_summary,
        generate_insights=request.generate_insights,
        generate_content_ideas=request.generate_content_ideas,
        export_formats=request.export_formats,
    )


# API Endpoints


@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "Research Configuration API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/configs", response_model=Dict[str, Any])
async def create_research_config(request: UserResearchConfigRequest):
    """Create a new research configuration"""
    try:
        config = convert_request_to_config(request)
        success = config_manager.create_config(config)

        if success:
            # Register with scheduler if auto-run is enabled
            if config.auto_run_enabled and config.schedule:
                scheduler.register_user_configs()

            return {
                "success": True,
                "message": f"Research configuration '{config.config_name}' created successfully",
                "config_name": config.config_name,
                "user_id": config.user_id,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create configuration")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/configs/{user_id}", response_model=List[str])
async def list_user_configs(user_id: str):
    """List all configurations for a user"""
    try:
        configs = config_manager.list_user_configs(user_id)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list configurations: {str(e)}")


@app.get("/configs/{user_id}/{config_name}", response_model=Dict[str, Any])
async def get_research_config(user_id: str, config_name: str):
    """Get a specific research configuration"""
    try:
        config = config_manager.load_config(user_id, config_name)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Convert to dict for JSON response
        from dataclasses import asdict

        return asdict(config)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load configuration: {str(e)}")


@app.put("/configs/{user_id}/{config_name}", response_model=Dict[str, Any])
async def update_research_config(user_id: str, config_name: str, updates: ConfigUpdateRequest):
    """Update an existing research configuration"""
    try:
        # Convert updates to dict, excluding None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}

        # Convert nested objects if present
        if "reddit_config" in update_dict and update_dict["reddit_config"]:
            update_dict["reddit_config"] = RedditConfig(**update_dict["reddit_config"])
        if "linkedin_config" in update_dict and update_dict["linkedin_config"]:
            update_dict["linkedin_config"] = LinkedInConfig(**update_dict["linkedin_config"])
        if "twitter_config" in update_dict and update_dict["twitter_config"]:
            update_dict["twitter_config"] = TwitterConfig(**update_dict["twitter_config"])
        if "schedule" in update_dict and update_dict["schedule"]:
            update_dict["schedule"] = ResearchSchedule(**update_dict["schedule"])

        success = config_manager.update_config(user_id, config_name, update_dict)

        if success:
            # Re-register with scheduler if schedule was updated
            if "schedule" in update_dict or "auto_run_enabled" in update_dict:
                scheduler.register_user_configs()

            return {
                "success": True,
                "message": f"Configuration '{config_name}' updated successfully",
                "updated_fields": list(update_dict.keys()),
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update configuration")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@app.delete("/configs/{user_id}/{config_name}", response_model=Dict[str, Any])
async def delete_research_config(user_id: str, config_name: str):
    """Delete a research configuration"""
    try:
        success = config_manager.delete_config(user_id, config_name)

        if success:
            # Re-register with scheduler to remove deleted config
            scheduler.register_user_configs()

            return {"success": True, "message": f"Configuration '{config_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Configuration not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")


@app.post("/jobs/trigger/{user_id}/{config_name}", response_model=Dict[str, Any])
async def trigger_research_job(user_id: str, config_name: str, background_tasks: BackgroundTasks):
    """Manually trigger a research job"""
    try:
        success = scheduler.trigger_manual_job(user_id, config_name)

        if success:
            return {
                "success": True,
                "message": f"Research job triggered for '{config_name}'",
                "user_id": user_id,
                "config_name": config_name,
                "triggered_at": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to trigger research job")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger job: {str(e)}")


@app.get("/jobs/status", response_model=Dict[str, Any])
async def get_job_status(user_id: Optional[str] = None):
    """Get status of research jobs"""
    try:
        status = scheduler.get_job_status(user_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@app.get("/jobs/status/{user_id}", response_model=Dict[str, Any])
async def get_user_job_status(user_id: str):
    """Get job status for a specific user"""
    return await get_job_status(user_id)


@app.post("/scheduler/start", response_model=Dict[str, Any])
async def start_scheduler():
    """Start the research scheduler"""
    try:
        scheduler.register_user_configs()
        scheduler.start()
        return {"success": True, "message": "Research scheduler started", "started_at": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")


@app.post("/scheduler/stop", response_model=Dict[str, Any])
async def stop_scheduler():
    """Stop the research scheduler"""
    try:
        scheduler.stop()
        return {"success": True, "message": "Research scheduler stopped", "stopped_at": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")


@app.get("/templates", response_model=Dict[str, Any])
async def get_config_templates():
    """Get predefined configuration templates"""
    templates = {
        "ai_business_tools": {
            "name": "AI Business Tools Research",
            "description": "Daily research on AI automation and business productivity tools",
            "enabled_sources": ["reddit", "linkedin"],
            "reddit_config": {
                "subreddits": ["artificial", "productivity", "Entrepreneur", "SaaS"],
                "search_topics": ["AI automation", "business tools", "productivity software"],
                "max_posts_per_subreddit": 8,
                "max_comments_per_post": 30,
            },
            "schedule": {"frequency": "daily", "time_of_day": "08:00"},
            "focus_areas": ["business_intelligence", "competitive_analysis", "trend_analysis"],
        },
        "competitive_intelligence": {
            "name": "Competitive Intelligence",
            "description": "Weekly deep dive into competitor activities and market trends",
            "enabled_sources": ["reddit", "twitter", "linkedin"],
            "reddit_config": {
                "subreddits": ["startups", "Entrepreneur", "SaaS", "business"],
                "search_topics": ["competitor analysis", "market research", "business strategy"],
                "max_posts_per_subreddit": 15,
                "max_comments_per_post": 50,
            },
            "schedule": {"frequency": "weekly", "time_of_day": "09:00", "days_of_week": [0]},  # Monday
            "analysis_depth": "comprehensive",
            "focus_areas": ["competitive_analysis", "market_intelligence", "business_strategy"],
        },
        "content_inspiration": {
            "name": "Content Ideas Generation",
            "description": "Bi-weekly research for LinkedIn content ideas and trending topics",
            "enabled_sources": ["reddit", "linkedin"],
            "reddit_config": {
                "subreddits": ["marketing", "socialmedia", "content", "copywriting"],
                "search_topics": ["content marketing", "LinkedIn tips", "social media strategy"],
                "max_posts_per_subreddit": 12,
                "max_comments_per_post": 20,
            },
            "schedule": {"frequency": "biweekly", "time_of_day": "10:00"},
            "focus_areas": ["trend_analysis", "content_opportunities"],
            "generate_content_ideas": True,
        },
    }

    return {"templates": templates, "count": len(templates)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
