"""
Avatar Management Service
Handles avatar profiles, script generation, and video creation
Integrated from TikClip functionality
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
import structlog
from anthropic import Anthropic

from database.supabase_client import SupabaseClient
from models.avatar_models import (
    AspectRatio,
    AvatarProfile,
    AvatarType,
    HeyGenAvatarData,
    HeyGenTalkingPhotoData,
    HeyGenVoiceData,
    ScriptGeneration,
    SubscriptionTier,
    UserVideoLimits,
    VideoGeneration,
    VideoStatus,
)
from utils.heygen_client import HeyGenClient

logger = structlog.get_logger(__name__)


class AvatarService:
    """Service for managing avatars, scripts, and video generation"""

    def __init__(self):
        """Initialize the avatar service"""
        self.db_client = SupabaseClient()
        self.heygen_client = HeyGenClient()

        # Initialize Anthropic client for script generation
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=anthropic_api_key)
            self.claude_model = "claude-3-5-sonnet-20241022"
        else:
            self.anthropic_client = None
            logger.warning("ANTHROPIC_API_KEY not set - script generation will be disabled")

        logger.info("Avatar service initialized")

    # Avatar Profile Management
    async def get_avatar_profiles(
        self, workspace_id: str, avatar_type: Optional[AvatarType] = None
    ) -> List[AvatarProfile]:
        """Get all avatar profiles for a workspace"""
        try:
            query = (
                self.db_client.service_client.table("avatar_profiles")
                .select("*")
                .eq("workspace_id", workspace_id)
                .order("display_order")
            )

            if avatar_type:
                query = query.eq("avatar_type", avatar_type.value)

            result = await query.execute()

            profiles = []
            for profile_data in result.data or []:
                profiles.append(AvatarProfile(**profile_data))

            return profiles

        except Exception as e:
            logger.error("Failed to get avatar profiles", error=str(e))
            return []

    async def create_avatar_profile(
        self,
        workspace_id: str,
        name: str,
        avatar_id: str,
        voice_id: str,
        avatar_type: AvatarType = AvatarType.TALKING_PHOTO,
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> Optional[AvatarProfile]:
        """Create a new avatar profile"""
        try:
            # If this is set as default, unset other defaults
            if is_default:
                await self._unset_default_avatars(workspace_id)

            # Get preview URL from HeyGen
            preview_url = await self._get_avatar_preview_url(avatar_id, avatar_type)

            profile_data = {
                "workspace_id": workspace_id,
                "name": name,
                "avatar_id": avatar_id,
                "voice_id": voice_id,
                "avatar_type": avatar_type.value,
                "description": description,
                "preview_url": preview_url,
                "is_default": is_default,
                "display_order": await self._get_next_display_order(workspace_id),
            }

            result = await self.db_client.service_client.table("avatar_profiles").insert(profile_data).execute()

            if result.data:
                return AvatarProfile(**result.data[0])

        except Exception as e:
            logger.error("Failed to create avatar profile", error=str(e))

        return None

    async def update_avatar_profile(self, profile_id: int, workspace_id: str, **updates) -> Optional[AvatarProfile]:
        """Update an avatar profile"""
        try:
            # If setting as default, unset other defaults
            if updates.get("is_default"):
                await self._unset_default_avatars(workspace_id)

            result = (
                await self.db_client.service_client.table("avatar_profiles")
                .update(updates)
                .eq("id", profile_id)
                .eq("workspace_id", workspace_id)
                .execute()
            )

            if result.data:
                return AvatarProfile(**result.data[0])

        except Exception as e:
            logger.error("Failed to update avatar profile", error=str(e))

        return None

    async def delete_avatar_profile(self, profile_id: int, workspace_id: str) -> bool:
        """Delete an avatar profile"""
        try:
            await self.db_client.service_client.table("avatar_profiles").delete().eq("id", profile_id).eq(
                "workspace_id", workspace_id
            ).execute()

            return True

        except Exception as e:
            logger.error("Failed to delete avatar profile", error=str(e))
            return False

    async def get_default_avatar_profile(self, workspace_id: str) -> Optional[AvatarProfile]:
        """Get the default avatar profile for a workspace"""
        try:
            result = (
                await self.db_client.service_client.table("avatar_profiles")
                .select("*")
                .eq("workspace_id", workspace_id)
                .eq("is_default", True)
                .execute()
            )

            if result.data:
                return AvatarProfile(**result.data[0])

            # If no default, get the first one
            result = (
                await self.db_client.service_client.table("avatar_profiles")
                .select("*")
                .eq("workspace_id", workspace_id)
                .order("display_order")
                .limit(1)
                .execute()
            )

            if result.data:
                return AvatarProfile(**result.data[0])

        except Exception as e:
            logger.error("Failed to get default avatar profile", error=str(e))

        return None

    # Script Generation
    async def generate_script(
        self,
        user_id: str,
        workspace_id: str,
        topic: str,
        target_audience: str = "general audience",
        video_style: str = "professional",
        duration_target: int = 60,
        additional_context: Optional[str] = None,
    ) -> Optional[ScriptGeneration]:
        """Generate a video script using AI"""
        if not self.anthropic_client:
            logger.error("Anthropic client not available for script generation")
            return None

        try:
            # Create the prompt for script generation
            prompt = self._build_script_prompt(topic, target_audience, video_style, duration_target, additional_context)

            # Generate script using Claude
            message = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=self.claude_model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            script_content = message.content[0].text

            # Calculate quality score (simple heuristic)
            quality_score = self._calculate_script_quality(script_content, duration_target)

            # Store the script
            script_data = {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "topic": topic,
                "script": script_content,
                "target_audience": target_audience,
                "video_style": video_style,
                "duration_target": duration_target,
                "model_used": self.claude_model,
                "quality_score": quality_score,
                "metadata": {
                    "additional_context": additional_context,
                    "word_count": len(script_content.split()),
                    "estimated_duration": self._estimate_script_duration(script_content),
                },
            }

            result = await self.db_client.service_client.table("script_generations").insert(script_data).execute()

            if result.data:
                return ScriptGeneration(**result.data[0])

        except Exception as e:
            logger.error("Failed to generate script", error=str(e))

        return None

    async def get_user_scripts(self, user_id: str, workspace_id: str, limit: int = 20) -> List[ScriptGeneration]:
        """Get user's generated scripts"""
        try:
            result = (
                await self.db_client.service_client.table("script_generations")
                .select("*")
                .eq("user_id", user_id)
                .eq("workspace_id", workspace_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            scripts = []
            for script_data in result.data or []:
                scripts.append(ScriptGeneration(**script_data))

            return scripts

        except Exception as e:
            logger.error("Failed to get user scripts", error=str(e))
            return []

    # Video Generation
    async def create_video(
        self,
        user_id: str,
        workspace_id: str,
        script_text: str,
        profile_id: Optional[int] = None,
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE,
        background: Optional[str] = None,
        script_id: Optional[int] = None,
    ) -> Optional[VideoGeneration]:
        """Create a video using HeyGen"""
        try:
            # Check user video limits
            can_create, limit_info = await self._check_video_limits(user_id, workspace_id)
            if not can_create:
                logger.warning("User exceeded video limits", user_id=user_id, limits=limit_info)
                return None

            # Get avatar and voice IDs
            if profile_id:
                profile = await self._get_avatar_profile_by_id(profile_id, workspace_id)
                if profile:
                    avatar_id = profile.avatar_id
                    voice_id = profile.voice_id

            if not avatar_id or not voice_id:
                # Use default avatar
                default_profile = await self.get_default_avatar_profile(workspace_id)
                if default_profile:
                    avatar_id = default_profile.avatar_id
                    voice_id = default_profile.voice_id
                else:
                    logger.error("No avatar or voice ID available")
                    return None

            # Create video with HeyGen
            heygen_result = await self.heygen_client.create_video(
                script=script_text,
                avatar_id=avatar_id,
                voice_id=voice_id,
                background=background or "office",
                aspect_ratio=aspect_ratio.value,
            )

            if not heygen_result or not heygen_result.get("video_id"):
                logger.error("Failed to create video with HeyGen", result=heygen_result)
                return None

            # Store video generation record
            video_data = {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "script_id": script_id,
                "profile_id": profile_id,
                "heygen_video_id": heygen_result["video_id"],
                "status": VideoStatus.PROCESSING.value,
                "aspect_ratio": aspect_ratio.value,
                "avatar_id": avatar_id,
                "voice_id": voice_id,
                "metadata": {"background": background, "heygen_response": heygen_result},
            }

            result = await self.db_client.service_client.table("video_generations").insert(video_data).execute()

            if result.data:
                video_gen = VideoGeneration(**result.data[0])

                # Start background task to check video status
                asyncio.create_task(self._monitor_video_generation(video_gen.id, heygen_result["video_id"]))

                return video_gen

        except Exception as e:
            logger.error("Failed to create video", error=str(e))

        return None

    async def get_video_status(self, video_id: int, user_id: str) -> Optional[VideoGeneration]:
        """Get video generation status"""
        try:
            result = (
                await self.db_client.service_client.table("video_generations")
                .select("*")
                .eq("id", video_id)
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                return VideoGeneration(**result.data[0])

        except Exception as e:
            logger.error("Failed to get video status", error=str(e))

        return None

    async def get_user_videos(
        self, user_id: str, workspace_id: str, status: Optional[VideoStatus] = None, limit: int = 20
    ) -> List[VideoGeneration]:
        """Get user's generated videos"""
        try:
            query = (
                self.db_client.service_client.table("video_generations")
                .select("*")
                .eq("user_id", user_id)
                .eq("workspace_id", workspace_id)
                .order("created_at", desc=True)
                .limit(limit)
            )

            if status:
                query = query.eq("status", status.value)

            result = await query.execute()

            videos = []
            for video_data in result.data or []:
                videos.append(VideoGeneration(**video_data))

            return videos

        except Exception as e:
            logger.error("Failed to get user videos", error=str(e))
            return []

    # HeyGen Integration
    async def sync_heygen_avatars(self, workspace_id: str) -> Dict[str, int]:
        """Sync avatars from HeyGen API"""
        try:
            # Get avatars and talking photos from HeyGen
            avatars_data = await self._fetch_heygen_avatars()

            if not avatars_data:
                return {"error": "Failed to fetch avatars from HeyGen"}

            avatars = avatars_data.get("avatars", [])
            talking_photos = avatars_data.get("talking_photos", [])

            created_count = 0
            updated_count = 0

            # Process standard avatars
            for avatar in avatars:
                result = await self._sync_avatar_profile(workspace_id, avatar, AvatarType.AVATAR)
                if result == "created":
                    created_count += 1
                elif result == "updated":
                    updated_count += 1

            # Process talking photos
            for photo in talking_photos:
                result = await self._sync_avatar_profile(workspace_id, photo, AvatarType.TALKING_PHOTO)
                if result == "created":
                    created_count += 1
                elif result == "updated":
                    updated_count += 1

            return {
                "created": created_count,
                "updated": updated_count,
                "total_avatars": len(avatars),
                "total_talking_photos": len(talking_photos),
            }

        except Exception as e:
            logger.error("Failed to sync HeyGen avatars", error=str(e))
            return {"error": str(e)}

    # User Limits and Analytics
    async def get_user_video_limits(self, user_id: str, workspace_id: str) -> UserVideoLimits:
        """Get user's video generation limits"""
        try:
            # Get user subscription info (placeholder - implement based on your user system)
            subscription_tier = SubscriptionTier.FREE  # Default
            is_admin = False  # Check admin status

            # Get monthly limits based on tier
            monthly_limits = {
                SubscriptionTier.FREE: 1,
                SubscriptionTier.STARTER: 3,
                SubscriptionTier.CREATOR: 8,
                SubscriptionTier.CREATOR_PRO: 15,
                SubscriptionTier.ENTERPRISE: 50,
            }

            monthly_limit = monthly_limits.get(subscription_tier, 1)

            # Count videos this month
            now = datetime.utcnow()
            first_day = datetime(now.year, now.month, 1)

            result = (
                await self.db_client.service_client.table("video_generations")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("workspace_id", workspace_id)
                .gte("created_at", first_day.isoformat())
                .execute()
            )

            videos_this_month = result.count or 0

            return UserVideoLimits(
                subscription_tier=subscription_tier,
                monthly_limit=monthly_limit,
                videos_this_month=videos_this_month,
                remaining_videos=max(0, monthly_limit - videos_this_month),
                is_admin=is_admin,
            )

        except Exception as e:
            logger.error("Failed to get user video limits", error=str(e))
            return UserVideoLimits(
                subscription_tier=SubscriptionTier.FREE, monthly_limit=1, videos_this_month=0, remaining_videos=1
            )

    # Private Helper Methods
    async def _unset_default_avatars(self, workspace_id: str):
        """Unset all default avatars for a workspace"""
        await self.db_client.service_client.table("avatar_profiles").update({"is_default": False}).eq(
            "workspace_id", workspace_id
        ).eq("is_default", True).execute()

    async def _get_next_display_order(self, workspace_id: str) -> int:
        """Get the next display order for avatar profiles"""
        result = (
            await self.db_client.service_client.table("avatar_profiles")
            .select("display_order")
            .eq("workspace_id", workspace_id)
            .order("display_order", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]["display_order"] + 1
        return 0

    async def _get_avatar_preview_url(self, avatar_id: str, avatar_type: AvatarType) -> Optional[str]:
        """Get preview URL for an avatar from HeyGen"""
        try:
            avatars_data = await self._fetch_heygen_avatars()
            if not avatars_data:
                return None

            # Search in appropriate list
            search_list = (
                avatars_data.get("talking_photos", [])
                if avatar_type == AvatarType.TALKING_PHOTO
                else avatars_data.get("avatars", [])
            )

            for item in search_list:
                item_id = item.get("talking_photo_id" if avatar_type == AvatarType.TALKING_PHOTO else "avatar_id")
                if item_id == avatar_id:
                    return item.get("preview_video_url") or item.get("preview_image_url")

        except Exception as e:
            logger.error("Failed to get avatar preview URL", error=str(e))

        return None

    async def _fetch_heygen_avatars(self) -> Optional[Dict[str, Any]]:
        """Fetch avatars from HeyGen API"""
        try:
            headers = {"X-Api-Key": os.getenv("HEYGEN_API_KEY"), "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.heygen.com/v2/avatars", headers=headers, timeout=30.0)
                response.raise_for_status()

                return response.json().get("data", {})

        except Exception as e:
            logger.error("Failed to fetch HeyGen avatars", error=str(e))
            return None

    async def _sync_avatar_profile(
        self, workspace_id: str, avatar_data: Dict[str, Any], avatar_type: AvatarType
    ) -> str:
        """Sync a single avatar profile"""
        try:
            avatar_id = avatar_data.get("talking_photo_id" if avatar_type == AvatarType.TALKING_PHOTO else "avatar_id")
            if not avatar_id:
                return "skipped"

            # Check if profile exists
            result = (
                await self.db_client.service_client.table("avatar_profiles")
                .select("*")
                .eq("workspace_id", workspace_id)
                .eq("avatar_id", avatar_id)
                .execute()
            )

            profile_data = {
                "name": avatar_data.get("name", f"Avatar {avatar_id}"),
                "preview_url": avatar_data.get("preview_video_url") or avatar_data.get("preview_image_url"),
                "avatar_type": avatar_type.value,
            }

            if result.data:
                # Update existing
                await self.db_client.service_client.table("avatar_profiles").update(profile_data).eq(
                    "id", result.data[0]["id"]
                ).execute()
                return "updated"
            else:
                # Create new (need voice_id - use a default or fetch from voices API)
                profile_data.update(
                    {
                        "workspace_id": workspace_id,
                        "avatar_id": avatar_id,
                        "voice_id": "default_voice_id",  # TODO: Implement voice selection
                        "display_order": await self._get_next_display_order(workspace_id),
                    }
                )

                await self.db_client.service_client.table("avatar_profiles").insert(profile_data).execute()
                return "created"

        except Exception as e:
            logger.error("Failed to sync avatar profile", error=str(e))
            return "error"

    async def _get_avatar_profile_by_id(self, profile_id: int, workspace_id: str) -> Optional[AvatarProfile]:
        """Get avatar profile by ID"""
        try:
            result = (
                await self.db_client.service_client.table("avatar_profiles")
                .select("*")
                .eq("id", profile_id)
                .eq("workspace_id", workspace_id)
                .execute()
            )

            if result.data:
                return AvatarProfile(**result.data[0])

        except Exception as e:
            logger.error("Failed to get avatar profile by ID", error=str(e))

        return None

    async def _check_video_limits(self, user_id: str, workspace_id: str) -> Tuple[bool, UserVideoLimits]:
        """Check if user can create more videos"""
        limits = await self.get_user_video_limits(user_id, workspace_id)

        # Admin users bypass limits
        if limits.is_admin:
            return True, limits

        # Check remaining videos
        return limits.remaining_videos > 0, limits

    async def _monitor_video_generation(self, video_id: int, heygen_video_id: str):
        """Monitor video generation status in background"""
        try:
            max_attempts = 60  # 5 minutes with 5-second intervals
            attempt = 0

            while attempt < max_attempts:
                await asyncio.sleep(5)  # Wait 5 seconds between checks

                # Check status with HeyGen
                status_result = await self.heygen_client.get_video_status(heygen_video_id)

                if not status_result:
                    attempt += 1
                    continue

                status = status_result.get("status", "processing").lower()

                update_data = {"metadata": status_result}

                if status == "completed":
                    update_data.update(
                        {
                            "status": VideoStatus.COMPLETED.value,
                            "video_url": status_result.get("video_url"),
                            "thumbnail_url": status_result.get("thumbnail_url"),
                            "duration": status_result.get("duration"),
                            "completed_at": datetime.utcnow().isoformat(),
                        }
                    )

                    await self.db_client.service_client.table("video_generations").update(update_data).eq(
                        "id", video_id
                    ).execute()

                    logger.info("Video generation completed", video_id=video_id)
                    break

                elif status == "failed" or status == "error":
                    update_data.update(
                        {
                            "status": VideoStatus.FAILED.value,
                            "error_message": status_result.get("error", "Video generation failed"),
                            "completed_at": datetime.utcnow().isoformat(),
                        }
                    )

                    await self.db_client.service_client.table("video_generations").update(update_data).eq(
                        "id", video_id
                    ).execute()

                    logger.error("Video generation failed", video_id=video_id, error=status_result.get("error"))
                    break

                attempt += 1

            # If we've exceeded max attempts, mark as failed
            if attempt >= max_attempts:
                await self.db_client.service_client.table("video_generations").update(
                    {
                        "status": VideoStatus.FAILED.value,
                        "error_message": "Video generation timed out",
                        "completed_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", video_id).execute()

                logger.error("Video generation timed out", video_id=video_id)

        except Exception as e:
            logger.error("Error monitoring video generation", video_id=video_id, error=str(e))

    def _build_script_prompt(
        self,
        topic: str,
        target_audience: str,
        video_style: str,
        duration_target: int,
        additional_context: Optional[str] = None,
    ) -> str:
        """Build prompt for script generation"""

        prompt = f"""Create a compelling {duration_target}-second video script about "{topic}" for {target_audience}.

Style: {video_style}
Target Duration: {duration_target} seconds
Target Audience: {target_audience}

Requirements:
- Hook viewers in the first 3 seconds
- Clear, conversational language
- Engaging storytelling
- Strong call-to-action at the end
- Optimized for avatar/talking head video format
- Natural speech patterns and pacing

Structure:
[HOOK] (0-3 seconds) - Attention-grabbing opening
[MAIN CONTENT] (3-{duration_target-10} seconds) - Core message/story
[CALL TO ACTION] ({duration_target-10}-{duration_target} seconds) - Clear next step

"""

        if additional_context:
            prompt += f"\nAdditional Context: {additional_context}\n"

        prompt += """
Please write a natural, engaging script that would work well when spoken by an AI avatar. Focus on:
- Conversational tone
- Clear pronunciation
- Logical flow
- Emotional engagement
- Memorable key points

Return only the script text, no additional formatting or explanations."""

        return prompt

    def _calculate_script_quality(self, script: str, target_duration: int) -> float:
        """Calculate a quality score for the generated script"""
        try:
            word_count = len(script.split())
            estimated_duration = self._estimate_script_duration(script)

            # Base score
            score = 0.7

            # Duration accuracy (closer to target = higher score)
            duration_diff = abs(estimated_duration - target_duration)
            if duration_diff <= 5:
                score += 0.2
            elif duration_diff <= 10:
                score += 0.1

            # Word count (reasonable range)
            if 50 <= word_count <= 200:
                score += 0.1

            # Has clear structure (look for hook/call-to-action indicators)
            if any(word in script.lower() for word in ["hook", "attention", "imagine", "what if"]):
                score += 0.05

            if any(word in script.lower() for word in ["subscribe", "follow", "like", "share", "comment"]):
                score += 0.05

            return min(1.0, score)

        except Exception:
            return 0.5

    def _estimate_script_duration(self, script: str) -> int:
        """Estimate script duration based on word count"""
        word_count = len(script.split())
        # Average speaking rate: ~150 words per minute = 2.5 words per second
        return int(word_count / 2.5)
