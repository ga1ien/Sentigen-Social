"""
Simplified Avatar Service for Railway deployment
Basic functionality without complex dependencies
"""

import os
from typing import List, Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class AvatarService:
    """Simplified avatar service for Railway deployment"""
    
    def __init__(self):
        """Initialize the avatar service"""
        logger.info("Avatar service initialized (simplified mode)")
    
    async def get_avatar_profiles(self, workspace_id: str, avatar_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get avatar profiles - simplified version"""
        # Return mock data for now
        return [
            {
                "id": 1,
                "name": "Professional Male",
                "avatar_id": "default_male",
                "voice_id": "default_male_voice",
                "avatar_type": "avatar",
                "is_default": True,
                "description": "Professional male avatar",
                "preview_url": None,
                "display_order": 0,
                "created_at": "2024-12-19T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Professional Female",
                "avatar_id": "default_female",
                "voice_id": "default_female_voice",
                "avatar_type": "avatar",
                "is_default": False,
                "description": "Professional female avatar",
                "preview_url": None,
                "display_order": 1,
                "created_at": "2024-12-19T00:00:00Z"
            }
        ]
    
    async def generate_script(
        self,
        user_id: str,
        workspace_id: str,
        topic: str,
        target_audience: str = "general audience",
        video_style: str = "professional",
        duration_target: int = 60,
        additional_context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate script - simplified version"""
        # Return mock script for now
        return {
            "id": 1,
            "topic": topic,
            "script": f"This is a sample script about {topic} for {target_audience}. The content would be generated using AI in the full implementation.",
            "target_audience": target_audience,
            "video_style": video_style,
            "duration_target": duration_target,
            "quality_score": 0.8,
            "created_at": "2024-12-19T00:00:00Z"
        }
    
    async def create_video(
        self,
        user_id: str,
        workspace_id: str,
        script_text: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Create video - simplified version"""
        # Return mock video creation response
        return {
            "id": 1,
            "heygen_video_id": "mock_video_123",
            "status": "processing",
            "aspect_ratio": "landscape",
            "created_at": "2024-12-19T00:00:00Z"
        }
    
    async def get_user_video_limits(self, user_id: str, workspace_id: str) -> Dict[str, Any]:
        """Get user video limits - simplified version"""
        return {
            "subscription_tier": "free",
            "monthly_limit": 1,
            "videos_this_month": 0,
            "remaining_videos": 1,
            "is_admin": False
        }
    
    async def get_user_scripts(self, user_id: str, workspace_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user scripts - simplified version"""
        return []
    
    async def get_user_videos(self, user_id: str, workspace_id: str, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user videos - simplified version"""
        return []
    
    async def get_video_status(self, video_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """Get video status - simplified version"""
        return None
    
    async def sync_heygen_avatars(self, workspace_id: str) -> Dict[str, Any]:
        """Sync HeyGen avatars - simplified version"""
        return {
            "created": 0,
            "updated": 0,
            "total_avatars": 0,
            "total_talking_photos": 0,
            "message": "HeyGen sync not implemented in simplified mode"
        }
