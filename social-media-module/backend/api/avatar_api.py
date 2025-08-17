"""
Avatar Management API
Handles avatar profiles, script generation, and video creation
Integrated from TikClip functionality
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from models.avatar_models import (
    AspectRatio,
    AvatarListResponse,
    AvatarProfile,
    AvatarType,
    ScriptGeneration,
    ScriptGenerationRequest,
    ScriptGenerationResponse,
    UserVideoLimits,
    VideoGeneration,
    VideoGenerationRequest,
    VideoGenerationResponse,
    VideoStatus,
    VideoStatusResponse,
)
from services.avatar_service import AvatarService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/avatars", tags=["Avatar Management"])

# Global avatar service instance (lazy initialization)
avatar_service = None


def get_avatar_service():
    global avatar_service
    if avatar_service is None:
        avatar_service = AvatarService()
    return avatar_service


# Request/Response Models
class CreateAvatarProfileRequest(BaseModel):
    """Request to create avatar profile"""

    name: str = Field(..., description="Display name for the avatar")
    avatar_id: str = Field(..., description="HeyGen avatar ID")
    voice_id: str = Field(..., description="HeyGen voice ID")
    avatar_type: AvatarType = Field(default=AvatarType.TALKING_PHOTO, description="Type of avatar")
    description: Optional[str] = Field(None, description="Avatar description")
    is_default: bool = Field(default=False, description="Set as default avatar")


class UpdateAvatarProfileRequest(BaseModel):
    """Request to update avatar profile"""

    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    display_order: Optional[int] = None


class BulkVideoRequest(BaseModel):
    """Request to create multiple videos"""

    script_ids: List[int] = Field(..., description="List of script IDs to create videos for")
    profile_id: Optional[int] = Field(None, description="Avatar profile to use for all videos")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.LANDSCAPE, description="Video aspect ratio")


# Avatar Profile Endpoints
@router.get("/profiles", response_model=AvatarListResponse)
async def get_avatar_profiles(
    workspace_id: str = "default_workspace", avatar_type: Optional[AvatarType] = None  # TODO: Get from auth
):
    """Get all avatar profiles for a workspace"""
    try:
        service = get_avatar_service()
        profiles = await service.get_avatar_profiles(workspace_id, avatar_type)
        # Simplified - no default profile lookup for now

        return AvatarListResponse(
            avatars=profiles,
            total_count=len(profiles),
            default_avatar_id=1,  # Simplified - always use first avatar as default
        )

    except Exception as e:
        logger.error("Failed to get avatar profiles", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles", response_model=AvatarProfile)
async def create_avatar_profile(
    request: CreateAvatarProfileRequest, workspace_id: str = "default_workspace"  # TODO: Get from auth
):
    """Create a new avatar profile"""
    try:
        profile = await avatar_service.create_avatar_profile(
            workspace_id=workspace_id,
            name=request.name,
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            avatar_type=request.avatar_type,
            description=request.description,
            is_default=request.is_default,
        )

        if not profile:
            raise HTTPException(status_code=400, detail="Failed to create avatar profile")

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create avatar profile", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profiles/{profile_id}", response_model=AvatarProfile)
async def update_avatar_profile(
    profile_id: int, request: UpdateAvatarProfileRequest, workspace_id: str = "default_workspace"  # TODO: Get from auth
):
    """Update an avatar profile"""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}

        profile = await avatar_service.update_avatar_profile(
            profile_id=profile_id, workspace_id=workspace_id, **updates
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Avatar profile not found")

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update avatar profile", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{profile_id}")
async def delete_avatar_profile(profile_id: int, workspace_id: str = "default_workspace"):  # TODO: Get from auth
    """Delete an avatar profile"""
    try:
        success = await avatar_service.delete_avatar_profile(profile_id, workspace_id)

        if not success:
            raise HTTPException(status_code=404, detail="Avatar profile not found")

        return {"message": "Avatar profile deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete avatar profile", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-heygen")
async def sync_heygen_avatars(workspace_id: str = "default_workspace"):  # TODO: Get from auth
    """Sync avatars from HeyGen API"""
    try:
        result = await avatar_service.sync_heygen_avatars(workspace_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "message": "HeyGen avatars synced successfully",
            "created": result["created"],
            "updated": result["updated"],
            "total_avatars": result["total_avatars"],
            "total_talking_photos": result["total_talking_photos"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to sync HeyGen avatars", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Script Generation Endpoints
@router.post("/scripts/generate", response_model=ScriptGenerationResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    user_id: str = "default_user",  # TODO: Get from auth
    workspace_id: str = "default_workspace",  # TODO: Get from auth
):
    """Generate a video script using AI"""
    try:
        service = get_avatar_service()
        script = await service.generate_script(
            user_id=user_id,
            workspace_id=workspace_id,
            topic=request.topic,
            target_audience=request.target_audience,
            video_style=request.video_style,
            duration_target=request.duration_target,
            additional_context=request.additional_context,
        )

        if not script:
            raise HTTPException(status_code=400, detail="Failed to generate script")

        # Calculate estimated duration and suggestions
        estimated_duration = len(script.script.split()) // 2.5  # ~2.5 words per second

        suggestions = []
        if estimated_duration > request.duration_target + 10:
            suggestions.append("Consider shortening the script for better pacing")
        elif estimated_duration < request.duration_target - 10:
            suggestions.append("Consider adding more detail or examples")

        return ScriptGenerationResponse(
            script_id=script.id,
            script=script.script,
            topic=script.topic,
            estimated_duration=int(estimated_duration),
            quality_score=script.quality_score or 0.5,
            suggestions=suggestions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate script", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scripts", response_model=List[ScriptGeneration])
async def get_user_scripts(
    user_id: str = "default_user",  # TODO: Get from auth
    workspace_id: str = "default_workspace",  # TODO: Get from auth
    limit: int = Query(default=20, le=100, description="Maximum number of scripts to return"),
):
    """Get user's generated scripts"""
    try:
        scripts = await avatar_service.get_user_scripts(user_id, workspace_id, limit)
        return scripts

    except Exception as e:
        logger.error("Failed to get user scripts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scripts/{script_id}", response_model=ScriptGeneration)
async def get_script(script_id: int, user_id: str = "default_user"):  # TODO: Get from auth
    """Get a specific script"""
    try:
        # TODO: Implement get_script method in avatar_service
        raise HTTPException(status_code=501, detail="Not implemented yet")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get script", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Video Generation Endpoints
@router.post("/videos/create", response_model=VideoGenerationResponse)
async def create_video(
    request: VideoGenerationRequest,
    user_id: str = "default_user",  # TODO: Get from auth
    workspace_id: str = "default_workspace",  # TODO: Get from auth
):
    """Create a video using HeyGen"""
    try:
        # Get script text
        script_text = request.script_text
        if not script_text and request.script_id:
            # TODO: Get script from database
            pass

        if not script_text:
            raise HTTPException(status_code=400, detail="Script text or script_id is required")

        video = await avatar_service.create_video(
            user_id=user_id,
            workspace_id=workspace_id,
            script_text=script_text,
            profile_id=request.profile_id,
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            aspect_ratio=request.aspect_ratio,
            background=request.additional_settings.get("background"),
            script_id=request.script_id,
        )

        if not video:
            raise HTTPException(status_code=400, detail="Failed to create video")

        return VideoGenerationResponse(
            video_id=video.id,
            heygen_video_id=video.heygen_video_id,
            status=video.status,
            estimated_completion_time=120,  # 2 minutes estimate
            message="Video generation started successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create video", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/bulk-create")
async def create_bulk_videos(
    request: BulkVideoRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "default_user",  # TODO: Get from auth
    workspace_id: str = "default_workspace",  # TODO: Get from auth
):
    """Create multiple videos from scripts"""
    try:
        # Check user limits
        limits = await avatar_service.get_user_video_limits(user_id, workspace_id)

        if len(request.script_ids) > limits.remaining_videos and not limits.is_admin:
            raise HTTPException(
                status_code=400, detail=f"Insufficient video credits. You have {limits.remaining_videos} remaining."
            )

        # Start bulk creation in background
        background_tasks.add_task(
            _create_bulk_videos_background,
            request.script_ids,
            request.profile_id,
            request.aspect_ratio,
            user_id,
            workspace_id,
        )

        return {
            "message": f"Bulk video creation started for {len(request.script_ids)} scripts",
            "script_count": len(request.script_ids),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start bulk video creation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: int, user_id: str = "default_user"):  # TODO: Get from auth
    """Get video generation status"""
    try:
        video = await avatar_service.get_video_status(video_id, user_id)

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Calculate progress based on status
        progress_map = {
            VideoStatus.PENDING: 0,
            VideoStatus.PROCESSING: 50,
            VideoStatus.COMPLETED: 100,
            VideoStatus.FAILED: 0,
            VideoStatus.CANCELLED: 0,
        }

        return VideoStatusResponse(
            video_id=video.id,
            heygen_video_id=video.heygen_video_id,
            status=video.status,
            progress=progress_map.get(video.status, 0),
            video_url=video.video_url,
            thumbnail_url=video.thumbnail_url,
            duration=video.duration,
            error_message=video.error_message,
            created_at=video.created_at,
            completed_at=video.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get video status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos", response_model=List[VideoGeneration])
async def get_user_videos(
    user_id: str = "default_user",  # TODO: Get from auth
    workspace_id: str = "default_workspace",  # TODO: Get from auth
    status: Optional[VideoStatus] = None,
    limit: int = Query(default=20, le=100, description="Maximum number of videos to return"),
):
    """Get user's generated videos"""
    try:
        videos = await avatar_service.get_user_videos(user_id, workspace_id, status, limit)
        return videos

    except Exception as e:
        logger.error("Failed to get user videos", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/videos/{video_id}")
async def delete_video(video_id: int, user_id: str = "default_user"):  # TODO: Get from auth
    """Delete a video"""
    try:
        # TODO: Implement delete_video method in avatar_service
        raise HTTPException(status_code=501, detail="Not implemented yet")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete video", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# User Limits and Analytics
@router.get("/limits", response_model=UserVideoLimits)
async def get_user_limits(
    user_id: str = "default_user", workspace_id: str = "default_workspace"  # TODO: Get from auth  # TODO: Get from auth
):
    """Get user's video generation limits"""
    try:
        limits = await avatar_service.get_user_video_limits(user_id, workspace_id)
        return limits

    except Exception as e:
        logger.error("Failed to get user limits", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/dashboard")
async def get_analytics_dashboard(
    user_id: str = "default_user", workspace_id: str = "default_workspace"  # TODO: Get from auth  # TODO: Get from auth
):
    """Get analytics dashboard data"""
    try:
        # TODO: Implement analytics dashboard
        return {
            "total_videos": 0,
            "total_scripts": 0,
            "videos_this_month": 0,
            "avg_video_duration": 0,
            "most_used_avatar": None,
            "recent_activity": [],
        }

    except Exception as e:
        logger.error("Failed to get analytics dashboard", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Health Check
@router.get("/health")
async def health_check():
    """Health check for avatar system"""
    try:
        return {
            "status": "healthy",
            "components": {"avatar_api": True, "service": "ready"},
            "message": "Avatar system is running (simplified mode)",
        }

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


# Background task functions
async def _create_bulk_videos_background(
    script_ids: List[int], profile_id: Optional[int], aspect_ratio: AspectRatio, user_id: str, workspace_id: str
):
    """Create multiple videos in background"""
    try:
        for script_id in script_ids:
            # TODO: Get script text from database
            script_text = f"Sample script for ID {script_id}"  # Placeholder

            await avatar_service.create_video(
                user_id=user_id,
                workspace_id=workspace_id,
                script_text=script_text,
                profile_id=profile_id,
                aspect_ratio=aspect_ratio,
                script_id=script_id,
            )

            # Small delay between videos to avoid rate limiting
            await asyncio.sleep(2)

        logger.info("Bulk video creation completed", script_count=len(script_ids), user_id=user_id)

    except Exception as e:
        logger.error("Bulk video creation failed", error=str(e))


# Include router in main app
def include_avatar_routes(app):
    """Include avatar routes in the main app"""
    app.include_router(router)
