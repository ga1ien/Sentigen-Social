#!/usr/bin/env python3
"""
Avatar Video Generation API
FastAPI service for creating avatar videos from research content
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from core.user_auth import UserContext, get_current_user
from services.avatar_video_system.avatar_video_service import (
    AvatarVideoService,
    ContentSource,
    ResearchVideoRequest,
    VideoGenerationConfig,
    VideoQuality,
    avatar_video_service,
)
from services.avatar_video_system.heygen_client import AspectRatio, VideoStatus

# Configure logging
logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Avatar Video Generation API",
    description="Create professional avatar videos from research content using HeyGen",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class CreateVideoRequest(BaseModel):
    script_title: Optional[str] = Field(None, description="Video title")
    script_content: str = Field(..., description="Script content for the video")
    avatar_profile_id: Optional[str] = Field(None, description="Avatar profile ID (uses default if not provided)")
    aspect_ratio: str = Field("portrait", description="Video aspect ratio: portrait, landscape, square")
    voice_speed: float = Field(1.0, description="Voice speed multiplier (0.5-2.0)")
    enable_captions: bool = Field(True, description="Enable video captions")
    background_color: str = Field("#ffffff", description="Background color (hex)")
    background_type: str = Field("color", description="Background type: color, image, video")
    background_url: Optional[str] = Field(None, description="Background asset URL")
    quality: str = Field("standard", description="Video quality: standard, high, premium")
    workspace_id: Optional[str] = Field(None, description="Workspace ID (optional)")


class CreateVideoFromResearchRequest(BaseModel):
    research_job_id: str = Field(..., description="Research job ID to create video from")
    avatar_profile_id: Optional[str] = Field(None, description="Avatar profile ID")
    aspect_ratio: str = Field("portrait", description="Video aspect ratio")
    voice_speed: float = Field(1.0, description="Voice speed multiplier")
    enable_captions: bool = Field(True, description="Enable video captions")
    title_override: Optional[str] = Field(None, description="Override video title")


class CreateCampaignRequest(BaseModel):
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    research_config_id: str = Field(..., description="Research configuration ID")
    source_tools: List[str] = Field(..., description="Research tools to use")
    avatar_profile_id: Optional[str] = Field(None, description="Default avatar profile")
    frequency: str = Field("daily", description="Campaign frequency: hourly, daily, weekly")
    max_videos_per_day: int = Field(3, description="Maximum videos per day")
    auto_post_enabled: bool = Field(False, description="Enable auto-posting")
    post_platforms: List[str] = Field(default_factory=list, description="Platforms for auto-posting")
    workspace_id: Optional[str] = Field(None, description="Workspace ID")


class VideoResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    script_title: Optional[str]
    script_content: str
    avatar_profile: Optional[Dict[str, Any]]
    heygen_video_id: str
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    status: str
    aspect_ratio: str
    duration_seconds: Optional[int]
    created_at: str
    completed_at: Optional[str]
    view_count: int
    download_count: int


class AvatarProfileResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    preview_url: Optional[str]
    avatar_type: str
    gender: Optional[str]
    age_range: Optional[str]
    style: Optional[str]
    subscription_tier: str


class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    frequency: str
    max_videos_per_day: int
    total_videos_generated: int
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    created_at: str


# WebSocket connection manager for real-time video status updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, video_id: str):
        await websocket.accept()
        self.active_connections[video_id] = websocket
        logger.info("WebSocket connected", video_id=video_id)

    def disconnect(self, video_id: str):
        if video_id in self.active_connections:
            del self.active_connections[video_id]
            logger.info("WebSocket disconnected", video_id=video_id)

    async def send_status_update(self, video_id: str, status_data: Dict[str, Any]):
        if video_id in self.active_connections:
            try:
                await self.active_connections[video_id].send_json(status_data)
            except Exception as e:
                logger.error("Failed to send WebSocket update", video_id=video_id, error=str(e))
                self.disconnect(video_id)


manager = ConnectionManager()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""

    # Check HeyGen API key
    heygen_api_key = os.getenv("HEYGEN_API_KEY")
    heygen_available = bool(heygen_api_key)

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "heygen_available": heygen_available,
        "service": "avatar_video_generation",
    }


# Avatar management endpoints
@app.get("/avatars", response_model=List[AvatarProfileResponse])
async def list_avatars(user_context: UserContext = Depends(get_current_user)):
    """List available avatar profiles for user"""
    try:
        avatars = await avatar_video_service.get_available_avatars(user_context.subscription_tier)

        return [
            AvatarProfileResponse(
                id=avatar["id"],
                name=avatar["name"],
                description=avatar.get("description"),
                preview_url=avatar.get("preview_url"),
                avatar_type=avatar["avatar_type"],
                gender=avatar.get("gender"),
                age_range=avatar.get("age_range"),
                style=avatar.get("style"),
                subscription_tier=avatar["subscription_tier"],
            )
            for avatar in avatars
        ]

    except Exception as e:
        logger.error("Failed to list avatars", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/avatars/{avatar_id}", response_model=AvatarProfileResponse)
async def get_avatar(avatar_id: str, user_context: UserContext = Depends(get_current_user)):
    """Get specific avatar profile"""
    try:
        avatar_profile = await avatar_video_service.get_avatar_profile(avatar_id)

        if not avatar_profile:
            raise HTTPException(status_code=404, detail="Avatar not found")

        # Check if user has access to this avatar tier
        user_tier = user_context.subscription_tier
        avatar_tier = avatar_profile.subscription_tier if hasattr(avatar_profile, "subscription_tier") else "free"

        tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
        if tier_hierarchy.get(user_tier, 0) < tier_hierarchy.get(avatar_tier, 0):
            raise HTTPException(status_code=403, detail="Avatar requires higher subscription tier")

        return AvatarProfileResponse(
            id=avatar_profile.id,
            name=avatar_profile.name,
            description=avatar_profile.description,
            preview_url=avatar_profile.preview_url,
            avatar_type=avatar_profile.avatar_type.value,
            gender=avatar_profile.gender,
            age_range=avatar_profile.age_range,
            style=avatar_profile.style,
            subscription_tier=avatar_tier,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get avatar", avatar_id=avatar_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Video generation endpoints
@app.post("/videos", response_model=Dict[str, str])
async def create_video(
    request: CreateVideoRequest,
    background_tasks: BackgroundTasks,
    user_context: UserContext = Depends(get_current_user),
):
    """Create avatar video from script content"""
    try:
        # Use provided workspace or default to first available
        workspace_id = request.workspace_id
        if not workspace_id and user_context.workspaces:
            workspace_id = user_context.workspaces[0]["id"]

        if not workspace_id:
            raise HTTPException(status_code=400, detail="No workspace available")

        # Create video generation config
        config = VideoGenerationConfig(
            avatar_profile_id=request.avatar_profile_id or "default",
            aspect_ratio=AspectRatio(request.aspect_ratio),
            voice_speed=request.voice_speed,
            enable_captions=request.enable_captions,
            background_color=request.background_color,
            background_type=request.background_type,
            background_url=request.background_url,
            quality=VideoQuality(request.quality),
            title=request.script_title,
        )

        # Create research video request
        video_request = ResearchVideoRequest(
            user_id=user_context.user_id,
            workspace_id=workspace_id,
            content_source=ContentSource.MANUAL,
            script_title=request.script_title,
            script_content=request.script_content,
            config=config,
        )

        # Create video
        video_id = await avatar_video_service.create_video_from_research(video_request)

        # Add background task to monitor video status
        background_tasks.add_task(monitor_video_status, video_id)

        return {"video_id": video_id, "status": "processing"}

    except Exception as e:
        logger.error("Failed to create video", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/videos/from-research", response_model=Dict[str, str])
async def create_video_from_research(
    request: CreateVideoFromResearchRequest,
    background_tasks: BackgroundTasks,
    user_context: UserContext = Depends(get_current_user),
):
    """Create avatar video from research job results"""
    try:
        # Create video generation config
        config = VideoGenerationConfig(
            avatar_profile_id=request.avatar_profile_id or "default",
            aspect_ratio=AspectRatio(request.aspect_ratio),
            voice_speed=request.voice_speed,
            enable_captions=request.enable_captions,
            title=request.title_override,
        )

        # Create video from research job
        video_id = await avatar_video_service.create_video_from_research_job(request.research_job_id, config)

        # Add background task to monitor video status
        background_tasks.add_task(monitor_video_status, video_id)

        return {"video_id": video_id, "status": "processing"}

    except Exception as e:
        logger.error("Failed to create video from research", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos", response_model=List[VideoResponse])
async def list_videos(
    workspace_id: Optional[str] = None, limit: int = 50, user_context: UserContext = Depends(get_current_user)
):
    """List user's avatar videos"""
    try:
        videos = await avatar_video_service.get_user_videos(user_context.user_id, workspace_id, limit)

        return [
            VideoResponse(
                id=video["id"],
                user_id=video["user_id"],
                workspace_id=video["workspace_id"],
                script_title=video.get("script_title"),
                script_content=video["script_content"],
                avatar_profile=video.get("avatar_profiles"),
                heygen_video_id=video["heygen_video_id"],
                video_url=video.get("video_url"),
                thumbnail_url=video.get("thumbnail_url"),
                status=video["status"],
                aspect_ratio=video["aspect_ratio"],
                duration_seconds=video.get("duration_seconds"),
                created_at=video["created_at"],
                completed_at=video.get("completed_at"),
                view_count=video.get("view_count", 0),
                download_count=video.get("download_count", 0),
            )
            for video in videos
        ]

    except Exception as e:
        logger.error("Failed to list videos", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, user_context: UserContext = Depends(get_current_user)):
    """Get specific video details"""
    try:
        video = await avatar_video_service.get_video_by_id(video_id, user_context.user_id)

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        return VideoResponse(
            id=video["id"],
            user_id=video["user_id"],
            workspace_id=video["workspace_id"],
            script_title=video.get("script_title"),
            script_content=video["script_content"],
            avatar_profile=video.get("avatar_profiles"),
            heygen_video_id=video["heygen_video_id"],
            video_url=video.get("video_url"),
            thumbnail_url=video.get("thumbnail_url"),
            status=video["status"],
            aspect_ratio=video["aspect_ratio"],
            duration_seconds=video.get("duration_seconds"),
            created_at=video["created_at"],
            completed_at=video.get("completed_at"),
            view_count=video.get("view_count", 0),
            download_count=video.get("download_count", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get video", video_id=video_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/videos/{video_id}")
async def delete_video(video_id: str, user_context: UserContext = Depends(get_current_user)):
    """Delete video"""
    try:
        success = await avatar_video_service.delete_video(video_id, user_context.user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Video not found")

        return {"message": "Video deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete video", video_id=video_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{video_id}/status")
async def get_video_status(video_id: str, user_context: UserContext = Depends(get_current_user)):
    """Get video generation status"""
    try:
        # Update status from HeyGen
        updated_video = await avatar_video_service.update_video_status(video_id)

        return {
            "video_id": video_id,
            "status": updated_video["status"],
            "video_url": updated_video.get("video_url"),
            "thumbnail_url": updated_video.get("thumbnail_url"),
            "duration_seconds": updated_video.get("duration_seconds"),
            "completed_at": updated_video.get("completed_at"),
            "error_message": updated_video.get("error_message"),
        }

    except Exception as e:
        logger.error("Failed to get video status", video_id=video_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Campaign management endpoints
@app.post("/campaigns", response_model=Dict[str, str])
async def create_campaign(request: CreateCampaignRequest, user_context: UserContext = Depends(get_current_user)):
    """Create automated video campaign"""
    try:
        # Use provided workspace or default to first available
        workspace_id = request.workspace_id
        if not workspace_id and user_context.workspaces:
            workspace_id = user_context.workspaces[0]["id"]

        if not workspace_id:
            raise HTTPException(status_code=400, detail="No workspace available")

        campaign_config = {
            "name": request.name,
            "description": request.description,
            "research_config_id": request.research_config_id,
            "source_tools": request.source_tools,
            "profile_id": request.avatar_profile_id,
            "frequency": request.frequency,
            "max_videos_per_day": request.max_videos_per_day,
            "auto_post_enabled": request.auto_post_enabled,
            "post_platforms": request.post_platforms,
        }

        campaign_id = await avatar_video_service.create_automated_video_campaign(
            user_context.user_id, workspace_id, campaign_config
        )

        return {"campaign_id": campaign_id}

    except Exception as e:
        logger.error("Failed to create campaign", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time video status updates
@app.websocket("/videos/{video_id}/status-ws")
async def video_status_websocket(websocket: WebSocket, video_id: str):
    """WebSocket endpoint for real-time video status updates"""
    await manager.connect(websocket, video_id)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(5)

            # Get current video status
            try:
                updated_video = await avatar_video_service.update_video_status(video_id)

                status_data = {
                    "video_id": video_id,
                    "status": updated_video["status"],
                    "video_url": updated_video.get("video_url"),
                    "thumbnail_url": updated_video.get("thumbnail_url"),
                    "completed_at": updated_video.get("completed_at"),
                    "timestamp": datetime.now().isoformat(),
                }

                await manager.send_status_update(video_id, status_data)

                # Stop polling if video is completed or failed
                if updated_video["status"] in ["completed", "failed", "error"]:
                    break

            except Exception as e:
                logger.error("Error in WebSocket status update", video_id=video_id, error=str(e))
                break

    except WebSocketDisconnect:
        manager.disconnect(video_id)


# Background task to monitor video status
async def monitor_video_status(video_id: str):
    """Background task to monitor video generation status"""
    max_attempts = 120  # 10 minutes max (5 second intervals)
    attempt = 0

    while attempt < max_attempts:
        try:
            updated_video = await avatar_video_service.update_video_status(video_id)

            # Send WebSocket update if connection exists
            status_data = {
                "video_id": video_id,
                "status": updated_video["status"],
                "video_url": updated_video.get("video_url"),
                "thumbnail_url": updated_video.get("thumbnail_url"),
                "completed_at": updated_video.get("completed_at"),
                "timestamp": datetime.now().isoformat(),
            }

            await manager.send_status_update(video_id, status_data)

            # Stop monitoring if video is completed or failed
            if updated_video["status"] in ["completed", "failed", "error"]:
                logger.info("Video monitoring completed", video_id=video_id, status=updated_video["status"])
                break

            await asyncio.sleep(5)  # Wait 5 seconds
            attempt += 1

        except Exception as e:
            logger.error("Error monitoring video status", video_id=video_id, error=str(e))
            await asyncio.sleep(5)
            attempt += 1

    if attempt >= max_attempts:
        logger.warning("Video monitoring timeout", video_id=video_id)


if __name__ == "__main__":
    uvicorn.run("avatar_video_api:app", host="0.0.0.0", port=8008, reload=True)  # Avatar video service port
