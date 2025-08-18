"""
Social Media Posting API
Handles creating, scheduling, and publishing posts to social media platforms
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from core.env_config import get_config
from core.user_auth import UserContext, get_current_user
from database.supabase_client import SupabaseClient
from utils.ayrshare_client import AyrshareClient

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/social-posting", tags=["social-posting"])

# Lazy initialization to avoid import-time environment variable issues
_config = None
_supabase_client = None


def get_app_config():
    """Get config with lazy initialization."""
    global _config
    if _config is None:
        _config = get_config()
    return _config


def get_supabase_client():
    """Get Supabase client with lazy initialization."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


class PostRequest(BaseModel):
    content: str = Field(..., description="Post content text")
    platforms: List[str] = Field(..., description="List of platforms to post to")
    media_urls: Optional[List[str]] = Field(None, description="URLs of media to include")
    schedule_date: Optional[datetime] = Field(None, description="When to schedule the post")
    platform_options: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Platform-specific options")


class PostResponse(BaseModel):
    id: str
    status: str
    platforms: List[str]
    scheduled_for: Optional[datetime]
    ayrshare_id: Optional[str]
    created_at: datetime


@router.post("/create", response_model=PostResponse)
async def create_post(post_request: PostRequest, current_user: UserContext = Depends(get_current_user)) -> PostResponse:
    """Create and optionally schedule a social media post."""
    try:
        logger.info(
            "Creating social media post",
            user_id=current_user.user_id,
            platforms=post_request.platforms,
            scheduled=bool(post_request.schedule_date),
        )

        # Validate platforms
        supported_platforms = ["linkedin", "twitter", "facebook", "instagram", "youtube"]
        invalid_platforms = [p for p in post_request.platforms if p.lower() not in supported_platforms]
        if invalid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported platforms: {invalid_platforms}"
            )

        # Check if user has connected accounts for requested platforms
        connected_result = (
            get_supabase_client()
            .client.table("social_media_accounts")
            .select("platform, is_connected")
            .eq("user_id", current_user.user_id)
            .in_("platform", post_request.platforms)
            .execute()
        )

        connected_platforms = (
            {acc["platform"] for acc in connected_result.data if acc["is_connected"]}
            if connected_result.data
            else set()
        )

        unconnected_platforms = set(post_request.platforms) - connected_platforms
        if unconnected_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Please connect these platforms first: {list(unconnected_platforms)}",
            )

        # Generate post ID
        post_id = str(uuid.uuid4())

        # Determine if this is immediate or scheduled
        is_scheduled = post_request.schedule_date is not None
        post_status = "scheduled" if is_scheduled else "publishing"

        # Store post in database
        post_data = {
            "id": post_id,
            "user_id": current_user.user_id,
            "content": post_request.content,
            "platforms": post_request.platforms,
            "media_urls": post_request.media_urls or [],
            "status": post_status,
            "scheduled_for": post_request.schedule_date.isoformat() if post_request.schedule_date else None,
            "platform_options": post_request.platform_options or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Insert into database
        db_result = get_supabase_client().client.table("social_media_posts").insert(post_data).execute()

        if not db_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save post to database"
            )

        ayrshare_id = None

        # If not scheduled, post immediately via Ayrshare
        if not is_scheduled:
            # Only attempt Ayrshare if configured
            config = get_app_config()
            if config.social_media.ayrshare_api_key:
                try:
                    ayrshare_client = AyrshareClient()
                    ayrshare_response = await ayrshare_client.post_to_social_media(
                        post_content=post_request.content,
                        platforms=post_request.platforms,
                        media_urls=post_request.media_urls,
                        platform_options=post_request.platform_options,
                    )

                    ayrshare_id = ayrshare_response.get("id")

                    # Update post with Ayrshare ID and success status
                    get_supabase_client().client.table("social_media_posts").update(
                        {
                            "ayrshare_id": ayrshare_id,
                            "status": "published",
                            "published_at": datetime.utcnow().isoformat(),
                            "ayrshare_response": ayrshare_response,
                        }
                    ).eq("id", post_id).execute()

                    post_status = "published"

                    logger.info("Post published successfully", post_id=post_id, ayrshare_id=ayrshare_id)

                except Exception as e:
                    logger.error("Failed to publish post via Ayrshare", post_id=post_id, error=str(e))

                    # Update post status to failed
                    get_supabase_client().client.table("social_media_posts").update(
                        {"status": "failed", "error_message": str(e), "updated_at": datetime.utcnow().isoformat()}
                    ).eq("id", post_id).execute()

                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to publish post: {str(e)}"
                    )

        return PostResponse(
            id=post_id,
            status=post_status,
            platforms=post_request.platforms,
            scheduled_for=post_request.schedule_date,
            ayrshare_id=ayrshare_id,
            created_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create post", user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create post")


@router.get("/posts")
async def get_user_posts(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    platform_filter: Optional[str] = None,
    current_user: UserContext = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get user's social media posts with optional filtering."""
    try:
        logger.info("Getting user posts", user_id=current_user.user_id, limit=limit, offset=offset)

        # Build query
        query = (
            get_supabase_client()
            .client.table("social_media_posts")
            .select(
                "id, content, platforms, status, scheduled_for, published_at, "
                "created_at, media_urls, engagement_metrics, ayrshare_id"
            )
            .eq("user_id", current_user.user_id)
        )

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)

        if platform_filter:
            query = query.contains("platforms", [platform_filter])

        # Apply pagination and ordering
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        posts = result.data if result.data else []

        # Get total count for pagination
        count_result = (
            get_supabase_client()
            .client.table("social_media_posts")
            .select("id", count="exact")
            .eq("user_id", current_user.user_id)
            .execute()
        )

        total_count = count_result.count if count_result.count else 0

        return {
            "posts": posts,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(posts) < total_count,
        }

    except Exception as e:
        logger.error("Failed to get user posts", user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve posts")


@router.get("/posts/{post_id}")
async def get_post_details(post_id: str, current_user: UserContext = Depends(get_current_user)) -> Dict[str, Any]:
    """Get detailed information about a specific post."""
    try:
        logger.info("Getting post details", post_id=post_id, user_id=current_user.user_id)

        # Get post from database
        result = (
            get_supabase_client()
            .client.table("social_media_posts")
            .select("*")
            .eq("id", post_id)
            .eq("user_id", current_user.user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        post = result.data[0]

        # If post has Ayrshare ID, get latest analytics
        if post.get("ayrshare_id"):
            config = get_app_config()
            if config.social_media.ayrshare_api_key:
                try:
                    ayrshare_client = AyrshareClient()
                    analytics = await ayrshare_client.get_post_analytics(post["ayrshare_id"])
                    post["live_analytics"] = analytics
                except Exception as e:
                    logger.warning("Failed to get live analytics", post_id=post_id, error=str(e))
                    post["live_analytics"] = None

        return post

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get post details", post_id=post_id, user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve post details")


@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, current_user: UserContext = Depends(get_current_user)) -> Dict[str, Any]:
    """Delete a post (only works for scheduled posts)."""
    try:
        logger.info("Deleting post", post_id=post_id, user_id=current_user.user_id)

        # Get post to check status
        result = (
            get_supabase_client()
            .client.table("social_media_posts")
            .select("status, ayrshare_id")
            .eq("id", post_id)
            .eq("user_id", current_user.user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        post = result.data[0]

        # Only allow deletion of scheduled or draft posts
        if post["status"] in ["published", "publishing"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete published posts")

        # Delete from database
        get_supabase_client().client.table("social_media_posts").delete().eq("id", post_id).eq(
            "user_id", current_user.user_id
        ).execute()

        return {"message": "Post deleted successfully", "post_id": post_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete post", post_id=post_id, user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete post")


@router.post("/posts/{post_id}/publish")
async def publish_scheduled_post(post_id: str, current_user: UserContext = Depends(get_current_user)) -> Dict[str, Any]:
    """Manually publish a scheduled post immediately."""
    try:
        logger.info("Publishing scheduled post", post_id=post_id, user_id=current_user.user_id)

        # Get post details
        result = (
            get_supabase_client()
            .client.table("social_media_posts")
            .select("*")
            .eq("id", post_id)
            .eq("user_id", current_user.user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        post = result.data[0]

        if post["status"] != "scheduled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Post status is '{post['status']}', can only publish scheduled posts",
            )

        # Publish via Ayrshare
        config = get_app_config()
        if config.social_media.ayrshare_api_key:
            ayrshare_client = AyrshareClient()
            ayrshare_response = await ayrshare_client.post_to_social_media(
                post_content=post["content"],
                platforms=post["platforms"],
                media_urls=post.get("media_urls"),
                platform_options=post.get("platform_options"),
            )

            # Update post status
            get_supabase_client().client.table("social_media_posts").update(
                {
                    "status": "published",
                    "published_at": datetime.utcnow().isoformat(),
                    "ayrshare_id": ayrshare_response.get("id"),
                    "ayrshare_response": ayrshare_response,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", post_id).execute()

            return {
                "message": "Post published successfully",
                "post_id": post_id,
                "ayrshare_id": ayrshare_response.get("id"),
                "published_at": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ayrshare API not configured")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to publish post", post_id=post_id, user_id=current_user.user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to publish post: {str(e)}"
        )
