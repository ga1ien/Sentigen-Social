"""
Social Media Account Management API
Handles connecting, managing, and monitoring social media accounts
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from core.env_config import get_config
from core.user_auth import UserContext, get_current_user
try:
    from database.supabase_client import SupabaseClient
except ModuleNotFoundError:
    from core.supabase_client import SupabaseClient
from utils.ayrshare_client import AyrshareClient

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/social-accounts", tags=["social-accounts"])

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


@router.get("/connected")
async def get_connected_accounts(current_user: UserContext = Depends(get_current_user)) -> Dict[str, Any]:
    """Get all connected social media accounts for the current user."""
    try:
        logger.info("Getting connected accounts", user_id=current_user.user_id)

        # Get user's social accounts from database
        result = (
            get_supabase_client()
            .client.table("social_media_accounts")
            .select("platform, username, is_connected, last_sync_at, follower_count, profile_data")
            .eq("user_id", current_user.user_id)
            .execute()
        )

        accounts = result.data if result.data else []

        # Also get real-time status from Ayrshare if configured
        ayrshare_accounts = []
        try:
            # Only attempt Ayrshare if configured
            config = get_app_config()
            if config.social_media.ayrshare_api_key:
                ayrshare_client = AyrshareClient()
                ayrshare_response = await ayrshare_client.get_connected_accounts()
                ayrshare_accounts = ayrshare_response.get("profiles", [])
        except Exception as e:
            logger.warning("Failed to get Ayrshare accounts", error=str(e))

        # Merge database and Ayrshare data
        platform_status = {
            "linkedin": {"connected": False, "username": "", "follower_count": 0},
            "twitter": {"connected": False, "username": "", "follower_count": 0},
            "facebook": {"connected": False, "username": "", "follower_count": 0},
            "instagram": {"connected": False, "username": "", "follower_count": 0},
            "youtube": {"connected": False, "username": "", "follower_count": 0},
        }

        # Update with database data
        for account in accounts:
            platform = account["platform"].lower()
            if platform in platform_status:
                platform_status[platform] = {
                    "connected": account["is_connected"],
                    "username": account["username"] or "",
                    "follower_count": account["follower_count"] or 0,
                    "last_sync": account["last_sync_at"],
                    "profile_data": account["profile_data"],
                }

        # Update with Ayrshare real-time data
        for ayr_account in ayrshare_accounts:
            platform = ayr_account.get("platform", "").lower()
            if platform in platform_status:
                platform_status[platform]["connected"] = True
                platform_status[platform]["ayrshare_status"] = "active"

        return {
            "accounts": platform_status,
            "total_connected": sum(1 for acc in platform_status.values() if acc["connected"]),
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("Failed to get connected accounts", user_id=current_user.user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve connected accounts"
        )


@router.post("/connect/{platform}")
async def connect_social_account(
    platform: str, current_user: UserContext = Depends(get_current_user)
) -> Dict[str, Any]:
    """Initiate connection to a social media platform."""
    try:
        platform = platform.lower()
        supported_platforms = ["linkedin", "twitter", "facebook", "instagram", "youtube"]

        if platform not in supported_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Platform '{platform}' not supported. Supported: {supported_platforms}",
            )

        logger.info("Initiating social account connection", user_id=current_user.user_id, platform=platform)

        # For now, return connection instructions
        # In production, this would initiate OAuth flow
        connection_urls = {
            "linkedin": "https://app.ayrshare.com/connect/linkedin",
            "twitter": "https://app.ayrshare.com/connect/twitter",
            "facebook": "https://app.ayrshare.com/connect/facebook",
            "instagram": "https://app.ayrshare.com/connect/instagram",
            "youtube": "https://app.ayrshare.com/connect/youtube",
        }

        # Store connection attempt in database
        connection_data = {
            "user_id": current_user.user_id,
            "platform": platform,
            "is_connected": False,
            "connection_initiated_at": datetime.utcnow().isoformat(),
            "status": "pending",
        }

        # Upsert the social account record
        get_supabase_client().client.table("social_media_accounts").upsert(
            connection_data, on_conflict="user_id,platform"
        ).execute()

        return {
            "platform": platform,
            "connection_url": connection_urls.get(platform),
            "status": "pending",
            "instructions": f"Please visit the connection URL to authorize {platform.title()} access",
            "next_step": "After authorization, your account will be automatically connected",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to initiate social account connection",
            user_id=current_user.user_id,
            platform=platform,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate account connection"
        )


@router.delete("/disconnect/{platform}")
async def disconnect_social_account(
    platform: str, current_user: UserContext = Depends(get_current_user)
) -> Dict[str, Any]:
    """Disconnect a social media platform."""
    try:
        platform = platform.lower()

        logger.info("Disconnecting social account", user_id=current_user.user_id, platform=platform)

        # Update database record
        result = (
            get_supabase_client()
            .client.table("social_media_accounts")
            .update({"is_connected": False, "disconnected_at": datetime.utcnow().isoformat(), "status": "disconnected"})
            .eq("user_id", current_user.user_id)
            .eq("platform", platform)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"No {platform} account found to disconnect"
            )

        return {
            "platform": platform,
            "status": "disconnected",
            "message": f"{platform.title()} account has been disconnected",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to disconnect social account", user_id=current_user.user_id, platform=platform, error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disconnect account")


@router.post("/sync/{platform}")
async def sync_social_account(platform: str, current_user: UserContext = Depends(get_current_user)) -> Dict[str, Any]:
    """Sync account data from the social media platform."""
    try:
        platform = platform.lower()

        logger.info("Syncing social account data", user_id=current_user.user_id, platform=platform)

        # Check if account is connected
        result = (
            get_supabase_client()
            .client.table("social_media_accounts")
            .select("is_connected, platform")
            .eq("user_id", current_user.user_id)
            .eq("platform", platform)
            .execute()
        )

        if not result.data or not result.data[0]["is_connected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"{platform.title()} account is not connected"
            )

        # In production, this would fetch real data from platform APIs
        # For now, simulate sync
        sync_data = {
            "last_sync_at": datetime.utcnow().isoformat(),
            "sync_status": "completed",
            "follower_count": 0,  # Would be real data
            "profile_data": {
                "name": f"User {platform.title()} Profile",
                "bio": f"Connected {platform} account",
                "verified": False,
            },
        }

        # Update database
        get_supabase_client().client.table("social_media_accounts").update(sync_data).eq(
            "user_id", current_user.user_id
        ).eq("platform", platform).execute()

        return {
            "platform": platform,
            "status": "synced",
            "last_sync": sync_data["last_sync_at"],
            "message": f"{platform.title()} account data has been synced",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to sync social account", user_id=current_user.user_id, platform=platform, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync account data")


@router.get("/analytics/{platform}")
async def get_platform_analytics(
    platform: str, days: int = 30, current_user: UserContext = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics data for a specific platform."""
    try:
        platform = platform.lower()

        logger.info("Getting platform analytics", user_id=current_user.user_id, platform=platform, days=days)

        # Check if account is connected
        result = (
            get_supabase_client()
            .client.table("social_media_accounts")
            .select("is_connected")
            .eq("user_id", current_user.user_id)
            .eq("platform", platform)
            .execute()
        )

        if not result.data or not result.data[0]["is_connected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"{platform.title()} account is not connected"
            )

        # Get posts for this platform from the last N days
        posts_result = (
            get_supabase_client()
            .client.table("social_media_posts")
            .select("id, content, published_at, engagement_metrics")
            .eq("user_id", current_user.user_id)
            .eq("platform", platform)
            .gte("published_at", (datetime.utcnow() - datetime.timedelta(days=days)).isoformat())
            .execute()
        )

        posts = posts_result.data if posts_result.data else []

        # Calculate analytics
        total_posts = len(posts)
        total_engagement = sum(post.get("engagement_metrics", {}).get("total", 0) for post in posts)
        avg_engagement = total_engagement / total_posts if total_posts > 0 else 0

        return {
            "platform": platform,
            "period_days": days,
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "average_engagement": round(avg_engagement, 2),
            "posts": posts[:10],  # Return last 10 posts
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get platform analytics", user_id=current_user.user_id, platform=platform, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve analytics data"
        )
