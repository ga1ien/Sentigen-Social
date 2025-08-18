#!/usr/bin/env python3
"""
Avatar Video Service
Integrates research content with HeyGen avatar video generation
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import structlog

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from core.research_service import JobStatus, ResearchJob, get_research_service
from database.supabase_client import SupabaseClient
from services.avatar_video_system.heygen_client import (
    AspectRatio,
    AvatarProfile,
    AvatarType,
    HeyGenAPIError,
    HeyGenClient,
    VideoGenerationRequest,
    VideoGenerationResponse,
    VideoStatus,
)

# Configure logging
logger = structlog.get_logger(__name__)


class ContentSource(Enum):
    """Content sources for video generation"""

    RESEARCH = "research"
    MANUAL = "manual"
    IMPORTED = "imported"
    TEMPLATE = "template"


class VideoQuality(Enum):
    """Video quality settings"""

    STANDARD = "standard"
    HIGH = "high"
    PREMIUM = "premium"


@dataclass
class VideoGenerationConfig:
    """Configuration for video generation"""

    avatar_profile_id: str
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    voice_speed: float = 1.0
    enable_captions: bool = True
    background_color: str = "#ffffff"
    background_type: str = "color"
    background_url: Optional[str] = None
    quality: VideoQuality = VideoQuality.STANDARD
    title: Optional[str] = None


@dataclass
class ResearchVideoRequest:
    """Request to create video from research content"""

    user_id: str
    workspace_id: str
    research_job_id: Optional[str] = None
    content_source: ContentSource = ContentSource.RESEARCH
    source_tool: Optional[str] = None
    script_title: Optional[str] = None
    script_content: str = ""
    original_content: Optional[Dict[str, Any]] = None
    config: Optional[VideoGenerationConfig] = None


class AvatarVideoService:
    """Service for managing avatar video generation"""

    def __init__(self):
        self.supabase_client = SupabaseClient()
        self.heygen_client = None  # Will be initialized when needed
        logger.info("Avatar video service initialized")

    async def get_available_avatars(self, user_subscription_tier: str = "free") -> List[Dict[str, Any]]:
        """Get available avatars based on user subscription"""
        try:
            # Query avatars based on subscription tier
            query = self.supabase_client.service_client.table("avatar_profiles").select("*")

            if user_subscription_tier == "free":
                query = query.in_("subscription_tier", ["free"])
            elif user_subscription_tier == "pro":
                query = query.in_("subscription_tier", ["free", "pro"])
            else:  # enterprise
                query = query.in_("subscription_tier", ["free", "pro", "enterprise"])

            result = query.eq("is_active", True).order("display_order").execute()

            avatars = result.data if result.data else []
            logger.info("Retrieved available avatars", count=len(avatars), subscription_tier=user_subscription_tier)

            return avatars

        except Exception as e:
            logger.error("Failed to get available avatars", error=str(e))
            raise

    async def get_avatar_profile(self, profile_id: str) -> Optional[AvatarProfile]:
        """Get avatar profile by ID"""
        try:
            result = (
                self.supabase_client.service_client.table("avatar_profiles")
                .select("*")
                .eq("id", profile_id)
                .single()
                .execute()
            )

            if not result.data:
                return None

            profile_data = result.data
            return AvatarProfile(
                id=profile_data["id"],
                name=profile_data["name"],
                avatar_id=profile_data["avatar_id"],
                voice_id=profile_data["voice_id"],
                avatar_type=AvatarType(profile_data["avatar_type"]),
                description=profile_data.get("description"),
                preview_url=profile_data.get("preview_url"),
                gender=profile_data.get("gender"),
                age_range=profile_data.get("age_range"),
                style=profile_data.get("style"),
            )

        except Exception as e:
            logger.error("Failed to get avatar profile", profile_id=profile_id, error=str(e))
            return None

    async def get_default_avatar_profile(self) -> Optional[AvatarProfile]:
        """Get default avatar profile"""
        try:
            result = (
                self.supabase_client.service_client.table("avatar_profiles")
                .select("*")
                .eq("is_default", True)
                .single()
                .execute()
            )

            if not result.data:
                # Fallback to first active avatar
                result = (
                    self.supabase_client.service_client.table("avatar_profiles")
                    .select("*")
                    .eq("is_active", True)
                    .order("display_order")
                    .limit(1)
                    .execute()
                )
                if not result.data:
                    return None
                profile_data = result.data[0]
            else:
                profile_data = result.data

            return AvatarProfile(
                id=profile_data["id"],
                name=profile_data["name"],
                avatar_id=profile_data["avatar_id"],
                voice_id=profile_data["voice_id"],
                avatar_type=AvatarType(profile_data["avatar_type"]),
                description=profile_data.get("description"),
                preview_url=profile_data.get("preview_url"),
                gender=profile_data.get("gender"),
                age_range=profile_data.get("age_range"),
                style=profile_data.get("style"),
            )

        except Exception as e:
            logger.error("Failed to get default avatar profile", error=str(e))
            return None

    async def create_video_from_research(self, request: ResearchVideoRequest) -> str:
        """Create video from research content"""
        try:
            logger.info(
                "Creating video from research",
                user_id=request.user_id,
                content_source=request.content_source.value,
                script_length=len(request.script_content),
            )

            # Get avatar profile
            avatar_profile = None
            if request.config and request.config.avatar_profile_id:
                avatar_profile = await self.get_avatar_profile(request.config.avatar_profile_id)

            if not avatar_profile:
                avatar_profile = await self.get_default_avatar_profile()
                if not avatar_profile:
                    raise ValueError("No avatar profile available")

            # Prepare video generation config
            config = request.config or VideoGenerationConfig(avatar_profile_id=avatar_profile.id)

            # Create HeyGen request
            heygen_request = VideoGenerationRequest(
                script=request.script_content,
                avatar_profile=avatar_profile,
                aspect_ratio=config.aspect_ratio,
                voice_speed=config.voice_speed,
                enable_captions=config.enable_captions,
                background_color=config.background_color,
                background_type=config.background_type,
                background_url=config.background_url,
                title=config.title or request.script_title or "Research Video",
            )

            # Generate video with HeyGen
            async with HeyGenClient() as heygen_client:
                heygen_response = await heygen_client.generate_video(heygen_request)

            # Save video generation record
            video_record = {
                "user_id": request.user_id,
                "workspace_id": request.workspace_id,
                "research_job_id": request.research_job_id,
                "content_source": request.content_source.value,
                "source_tool": request.source_tool,
                "script_title": request.script_title,
                "script_content": request.script_content,
                "original_content": request.original_content,
                "profile_id": avatar_profile.id,
                "heygen_video_id": heygen_response.video_id,
                "status": heygen_response.status.value,
                "aspect_ratio": config.aspect_ratio.value,
                "voice_speed": config.voice_speed,
                "enable_captions": config.enable_captions,
                "background_color": config.background_color,
                "background_type": config.background_type,
                "background_url": config.background_url,
                "started_at": datetime.now().isoformat(),
            }

            result = self.supabase_client.service_client.table("video_generations").insert(video_record).execute()

            if not result.data:
                raise Exception("Failed to save video generation record")

            video_id = result.data[0]["id"]

            logger.info(
                "Video generation started",
                video_id=video_id,
                heygen_video_id=heygen_response.video_id,
                avatar_name=avatar_profile.name,
            )

            return video_id

        except Exception as e:
            logger.error("Failed to create video from research", error=str(e))
            raise

    async def update_video_status(self, video_id: str) -> Dict[str, Any]:
        """Update video status by checking with HeyGen"""
        try:
            # Get video record
            result = (
                self.supabase_client.service_client.table("video_generations")
                .select("*")
                .eq("id", video_id)
                .single()
                .execute()
            )

            if not result.data:
                raise ValueError(f"Video not found: {video_id}")

            video_record = result.data
            heygen_video_id = video_record["heygen_video_id"]

            # Check status with HeyGen
            async with HeyGenClient() as heygen_client:
                status_response = await heygen_client.get_video_status(heygen_video_id)

            # Update database record
            updates = {"status": status_response.status.value, "updated_at": datetime.now().isoformat()}

            if status_response.status == VideoStatus.COMPLETED:
                updates.update(
                    {
                        "video_url": status_response.video_url,
                        "thumbnail_url": status_response.thumbnail_url,
                        "duration_seconds": status_response.duration_seconds,
                        "completed_at": datetime.now().isoformat(),
                    }
                )
            elif status_response.status == VideoStatus.FAILED:
                updates["error_message"] = status_response.error_message

            # Update database
            update_result = (
                self.supabase_client.service_client.table("video_generations")
                .update(updates)
                .eq("id", video_id)
                .execute()
            )

            if not update_result.data:
                raise Exception("Failed to update video status")

            updated_record = update_result.data[0]

            logger.info(
                "Video status updated",
                video_id=video_id,
                status=status_response.status.value,
                has_video_url=bool(status_response.video_url),
            )

            return updated_record

        except Exception as e:
            logger.error("Failed to update video status", video_id=video_id, error=str(e))
            raise

    async def get_user_videos(
        self, user_id: str, workspace_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's video generations"""
        try:
            query = (
                self.supabase_client.service_client.table("video_generations")
                .select(
                    """
                *,
                avatar_profiles(name, description, preview_url)
            """
                )
                .eq("user_id", user_id)
            )

            if workspace_id:
                query = query.eq("workspace_id", workspace_id)

            result = query.order("created_at", desc=True).limit(limit).execute()

            videos = result.data if result.data else []

            logger.info("Retrieved user videos", user_id=user_id, count=len(videos))

            return videos

        except Exception as e:
            logger.error("Failed to get user videos", user_id=user_id, error=str(e))
            raise

    async def get_video_by_id(self, video_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific video by ID"""
        try:
            result = (
                self.supabase_client.service_client.table("video_generations")
                .select(
                    """
                *,
                avatar_profiles(name, description, preview_url)
            """
                )
                .eq("id", video_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )

            return result.data if result.data else None

        except Exception as e:
            logger.error("Failed to get video by ID", video_id=video_id, error=str(e))
            return None

    async def delete_video(self, video_id: str, user_id: str) -> bool:
        """Delete video generation record"""
        try:
            result = (
                self.supabase_client.service_client.table("video_generations")
                .delete()
                .eq("id", video_id)
                .eq("user_id", user_id)
                .execute()
            )

            success = bool(result.data)

            if success:
                logger.info("Video deleted", video_id=video_id, user_id=user_id)

            return success

        except Exception as e:
            logger.error("Failed to delete video", video_id=video_id, error=str(e))
            return False

    async def create_video_from_research_job(
        self, research_job_id: str, config: Optional[VideoGenerationConfig] = None
    ) -> str:
        """Create video from completed research job"""
        try:
            # Get research job
            job = await get_research_service().get_job_by_id(research_job_id)
            if not job:
                raise ValueError(f"Research job not found: {research_job_id}")

            if job.status != JobStatus.COMPLETED:
                raise ValueError(f"Research job not completed: {job.status.value}")

            # Load research results
            if not job.results_path:
                raise ValueError("Research job has no results")

            # Load results file
            try:
                with open(job.results_path, "r") as f:
                    research_data = json.load(f)
            except Exception as e:
                raise ValueError(f"Failed to load research results: {e}")

            # Extract content for video script
            script_content = await self._extract_script_from_research(research_data, job.source_type.value)

            if not script_content:
                raise ValueError("No suitable content found in research results")

            # Create video request
            request = ResearchVideoRequest(
                user_id=job.user_id,
                workspace_id=job.workspace_id,
                research_job_id=research_job_id,
                content_source=ContentSource.RESEARCH,
                source_tool=job.source_type.value,
                script_title=f"Research Video - {job.source_type.value.title()}",
                script_content=script_content,
                original_content=research_data,
                config=config,
            )

            return await self.create_video_from_research(request)

        except Exception as e:
            logger.error("Failed to create video from research job", research_job_id=research_job_id, error=str(e))
            raise

    async def _extract_script_from_research(self, research_data: Dict[str, Any], source_tool: str) -> str:
        """Extract video script content from research data"""
        try:
            script_parts = []

            if source_tool == "reddit":
                # Extract Reddit insights
                if "analysis" in research_data and "actionable_recommendations" in research_data["analysis"]:
                    recommendations = research_data["analysis"]["actionable_recommendations"][:3]

                    script_parts.append("Based on our latest Reddit research, here are the key insights:")

                    for i, rec in enumerate(recommendations, 1):
                        action = rec.get("action", "")
                        description = rec.get("description", "")
                        script_parts.append(f"{i}. {action}: {description}")

                    script_parts.append(
                        "These trends represent significant opportunities for content creators and businesses."
                    )

            elif source_tool == "hackernews":
                # Extract Hacker News insights
                if "analysis" in research_data and "content_opportunities" in research_data["analysis"]:
                    opportunities = research_data["analysis"]["content_opportunities"]

                    script_parts.append("Our Hacker News analysis reveals exciting tech trends:")

                    # Get top trending topics
                    if "trending_topics" in opportunities:
                        topics = opportunities["trending_topics"][:3]
                        for topic in topics:
                            title = topic.get("title", "")
                            score = topic.get("score", 0)
                            script_parts.append(f"Trending: {title} with {score} points")

            elif source_tool == "github":
                # Extract GitHub insights
                if "analysis" in research_data and "trending_repositories" in research_data["analysis"]:
                    repos = research_data["analysis"]["trending_repositories"][:3]

                    script_parts.append("GitHub trending analysis shows these hot repositories:")

                    for repo in repos:
                        name = repo.get("name", "")
                        description = repo.get("description", "")
                        stars = repo.get("stars", 0)
                        script_parts.append(f"{name}: {description}. {stars} stars and growing.")

            elif source_tool == "google_trends":
                # Extract Google Trends insights
                if "analysis" in research_data and "content_opportunities" in research_data["analysis"]:
                    opportunities = research_data["analysis"]["content_opportunities"]

                    script_parts.append("Google Trends analysis reveals these viral opportunities:")

                    # Get breakout topics
                    if "breakout_topics" in opportunities:
                        breakouts = opportunities["breakout_topics"][:3]
                        for breakout in breakouts:
                            query = breakout.get("query", "")
                            growth = breakout.get("growth", "")
                            script_parts.append(f"Breakout topic: {query} showing {growth} growth")

            # Join script parts
            script = " ".join(script_parts)

            # Ensure minimum length
            if len(script) < 50:
                script = f"Our research analysis has uncovered valuable insights. {script} This data-driven approach helps identify emerging trends and opportunities in the market."

            # Ensure maximum length for video generation
            if len(script) > 2000:
                script = script[:2000] + "..."

            logger.info("Extracted script from research", source_tool=source_tool, script_length=len(script))

            return script

        except Exception as e:
            logger.error("Failed to extract script from research", source_tool=source_tool, error=str(e))
            return f"Our {source_tool} research has revealed interesting insights and trends that are worth exploring further."

    async def create_automated_video_campaign(
        self, user_id: str, workspace_id: str, campaign_config: Dict[str, Any]
    ) -> str:
        """Create automated video campaign that generates videos from research"""
        try:
            campaign_data = {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "name": campaign_config.get("name", "Automated Video Campaign"),
                "description": campaign_config.get("description", ""),
                "research_config_id": campaign_config.get("research_config_id"),
                "source_tools": campaign_config.get("source_tools", []),
                "template_id": campaign_config.get("template_id"),
                "profile_id": campaign_config.get("profile_id"),
                "is_active": campaign_config.get("is_active", True),
                "frequency": campaign_config.get("frequency", "daily"),
                "max_videos_per_day": campaign_config.get("max_videos_per_day", 3),
                "min_content_score": campaign_config.get("min_content_score", 70),
                "content_filters": campaign_config.get("content_filters", {}),
                "auto_post_enabled": campaign_config.get("auto_post_enabled", False),
                "post_platforms": campaign_config.get("post_platforms", []),
                "post_schedule": campaign_config.get("post_schedule", {}),
                "next_run_at": datetime.now() + timedelta(hours=1),  # Start in 1 hour
            }

            result = self.supabase_client.service_client.table("video_campaigns").insert(campaign_data).execute()

            if not result.data:
                raise Exception("Failed to create video campaign")

            campaign_id = result.data[0]["id"]

            logger.info(
                "Video campaign created",
                campaign_id=campaign_id,
                user_id=user_id,
                frequency=campaign_config.get("frequency"),
            )

            return campaign_id

        except Exception as e:
            logger.error("Failed to create video campaign", error=str(e))
            raise

    async def process_video_campaigns(self):
        """Process active video campaigns (called by scheduler)"""
        try:
            # Get campaigns ready to run
            now = datetime.now()
            result = (
                self.supabase_client.service_client.table("video_campaigns")
                .select("*")
                .eq("is_active", True)
                .lte("next_run_at", now.isoformat())
                .execute()
            )

            campaigns = result.data if result.data else []

            logger.info("Processing video campaigns", count=len(campaigns))

            for campaign in campaigns:
                try:
                    await self._process_single_campaign(campaign)
                except Exception as e:
                    logger.error("Failed to process campaign", campaign_id=campaign["id"], error=str(e))

        except Exception as e:
            logger.error("Failed to process video campaigns", error=str(e))

    async def _process_single_campaign(self, campaign: Dict[str, Any]):
        """Process a single video campaign"""
        campaign_id = campaign["id"]

        try:
            # Get recent research jobs for this campaign
            research_config_id = campaign.get("research_config_id")
            if not research_config_id:
                logger.warning("Campaign has no research config", campaign_id=campaign_id)
                return

            # Get completed research jobs from the last 24 hours
            since = datetime.now() - timedelta(hours=24)
            jobs = await get_research_service().get_jobs_by_config(
                research_config_id, since=since, status=JobStatus.COMPLETED
            )

            if not jobs:
                logger.info("No recent research jobs for campaign", campaign_id=campaign_id)
                return

            # Check daily video limit
            today = datetime.now().date()
            daily_count = await self._get_daily_video_count(campaign["user_id"], today)
            max_daily = campaign.get("max_videos_per_day", 3)

            if daily_count >= max_daily:
                logger.info("Daily video limit reached", campaign_id=campaign_id, count=daily_count)
                return

            # Create videos from research jobs
            videos_created = 0
            for job in jobs[: max_daily - daily_count]:
                try:
                    # Create video config
                    config = VideoGenerationConfig(
                        avatar_profile_id=campaign.get("profile_id"),
                        aspect_ratio=AspectRatio.PORTRAIT,  # Default for social media
                        enable_captions=True,
                    )

                    video_id = await self.create_video_from_research_job(job.id, config)
                    videos_created += 1

                    logger.info(
                        "Campaign video created", campaign_id=campaign_id, video_id=video_id, research_job_id=job.id
                    )

                except Exception as e:
                    logger.error(
                        "Failed to create campaign video", campaign_id=campaign_id, research_job_id=job.id, error=str(e)
                    )

            # Update campaign next run time
            frequency = campaign.get("frequency", "daily")
            if frequency == "hourly":
                next_run = datetime.now() + timedelta(hours=1)
            elif frequency == "daily":
                next_run = datetime.now() + timedelta(days=1)
            elif frequency == "weekly":
                next_run = datetime.now() + timedelta(weeks=1)
            else:
                next_run = datetime.now() + timedelta(days=1)

            # Update campaign
            self.supabase_client.service_client.table("video_campaigns").update(
                {
                    "last_run_at": datetime.now().isoformat(),
                    "next_run_at": next_run.isoformat(),
                    "total_videos_generated": campaign.get("total_videos_generated", 0) + videos_created,
                }
            ).eq("id", campaign_id).execute()

            logger.info("Campaign processed", campaign_id=campaign_id, videos_created=videos_created, next_run=next_run)

        except Exception as e:
            logger.error("Failed to process campaign", campaign_id=campaign_id, error=str(e))

    async def _get_daily_video_count(self, user_id: str, date: datetime.date) -> int:
        """Get count of videos created by user on specific date"""
        try:
            start_of_day = datetime.combine(date, datetime.min.time())
            end_of_day = datetime.combine(date, datetime.max.time())

            result = (
                self.supabase_client.service_client.table("video_generations")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .gte("created_at", start_of_day.isoformat())
                .lte("created_at", end_of_day.isoformat())
                .execute()
            )

            return result.count or 0

        except Exception as e:
            logger.error("Failed to get daily video count", user_id=user_id, error=str(e))
            return 0


# Lazy initialization to avoid import-time environment variable issues
_avatar_video_service = None

def get_avatar_video_service():
    """Get avatar video service with lazy initialization."""
    global _avatar_video_service
    if _avatar_video_service is None:
        _avatar_video_service = AvatarVideoService()
    return _avatar_video_service


# Convenience functions
async def create_video_from_research_content(
    user_id: str,
    workspace_id: str,
    content: str,
    title: str = "Research Video",
    avatar_profile_id: Optional[str] = None,
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT,
) -> str:
    """Convenience function to create video from research content"""

    config = VideoGenerationConfig(
        avatar_profile_id=avatar_profile_id or "default", aspect_ratio=aspect_ratio, title=title
    )

    request = ResearchVideoRequest(
        user_id=user_id,
        workspace_id=workspace_id,
        content_source=ContentSource.RESEARCH,
        script_title=title,
        script_content=content,
        config=config,
    )

    return await get_avatar_video_service().create_video_from_research(request)


if __name__ == "__main__":

    async def test_avatar_video_service():
        """Test avatar video service"""
        try:
            # Test getting available avatars
            avatars = await get_avatar_video_service().get_available_avatars("free")
            print(f"✅ Found {len(avatars)} available avatars")

            # Test creating video from content
            test_content = """
            Based on our research analysis, AI automation tools are experiencing unprecedented growth.
            ChatGPT and similar platforms show over 300% increase in adoption.
            This presents massive opportunities for businesses to streamline operations and boost productivity.
            """

            video_id = await create_video_from_research_content(
                user_id="test-user",
                workspace_id="test-workspace",
                content=test_content,
                title="AI Trends Research Video",
            )

            print(f"✅ Video creation started: {video_id}")

        except Exception as e:
            print(f"❌ Test failed: {e}")

    # Run test
    asyncio.run(test_avatar_video_service())
