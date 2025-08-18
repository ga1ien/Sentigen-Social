#!/usr/bin/env python3
"""
Research to Video Integration
Automatically converts research findings into avatar videos
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from core.research_service import JobStatus, research_service
from services.avatar_video_system.avatar_video_service import (
    AspectRatio,
    ContentSource,
    ResearchVideoRequest,
    VideoGenerationConfig,
    avatar_video_service,
)
from services.avatar_video_system.heygen_client import VideoStatus

# Configure logging
logger = structlog.get_logger(__name__)


@dataclass
class ContentExtractionRule:
    """Rules for extracting content from research data"""

    source_tool: str
    content_paths: List[str]  # JSON paths to extract content
    title_template: str
    script_template: str
    min_content_length: int = 100
    max_content_length: int = 2000


class ResearchToVideoIntegrator:
    """Integrates research tools with avatar video generation"""

    def __init__(self):
        self.content_extraction_rules = self._initialize_extraction_rules()
        logger.info("Research to video integrator initialized")

    def _initialize_extraction_rules(self) -> Dict[str, ContentExtractionRule]:
        """Initialize content extraction rules for each research tool"""
        return {
            "reddit": ContentExtractionRule(
                source_tool="reddit",
                content_paths=[
                    "analysis.actionable_recommendations",
                    "analysis.key_insights",
                    "analysis.trending_topics",
                ],
                title_template="Reddit Research Insights - {topic}",
                script_template="""
                Based on our latest Reddit research, here are the key insights we discovered:

                {content}

                These trends represent significant opportunities for content creators and businesses
                looking to engage with their audience and capitalize on emerging discussions.
                """,
                min_content_length=150,
                max_content_length=1800,
            ),
            "hackernews": ContentExtractionRule(
                source_tool="hackernews",
                content_paths=[
                    "analysis.trending_stories",
                    "analysis.top_discussions",
                    "analysis.emerging_technologies",
                ],
                title_template="Hacker News Tech Trends - {topic}",
                script_template="""
                Our Hacker News analysis reveals the latest technology trends and discussions:

                {content}

                These insights from the tech community highlight emerging opportunities
                and innovations that are shaping the future of technology.
                """,
                min_content_length=150,
                max_content_length=1800,
            ),
            "github": ContentExtractionRule(
                source_tool="github",
                content_paths=[
                    "analysis.trending_repositories",
                    "analysis.popular_languages",
                    "analysis.emerging_projects",
                ],
                title_template="GitHub Development Trends - {topic}",
                script_template="""
                GitHub trending analysis shows these exciting developments in software:

                {content}

                These repositories and projects represent the cutting edge of software development
                and offer valuable insights into where the industry is heading.
                """,
                min_content_length=150,
                max_content_length=1800,
            ),
            "google_trends": ContentExtractionRule(
                source_tool="google_trends",
                content_paths=[
                    "analysis.content_opportunities.breakout_topics",
                    "analysis.content_opportunities.question_opportunities",
                    "analysis.trend_insights",
                ],
                title_template="Google Trends Analysis - {topic}",
                script_template="""
                Google Trends analysis reveals these viral opportunities and search insights:

                {content}

                These trending topics and search patterns provide valuable intelligence
                for content strategy and market positioning.
                """,
                min_content_length=150,
                max_content_length=1800,
            ),
        }

    async def create_video_from_research_job(
        self,
        research_job_id: str,
        avatar_profile_id: Optional[str] = None,
        aspect_ratio: AspectRatio = AspectRatio.PORTRAIT,
        voice_speed: float = 1.0,
        custom_title: Optional[str] = None,
    ) -> str:
        """Create avatar video from research job results"""

        try:
            logger.info("Creating video from research job", research_job_id=research_job_id)

            # Get research job
            job = await research_service.get_job_by_id(research_job_id)
            if not job:
                raise ValueError(f"Research job not found: {research_job_id}")

            if job.status != JobStatus.COMPLETED:
                raise ValueError(f"Research job not completed: {job.status.value}")

            # Load research results
            if not job.results_path or not os.path.exists(job.results_path):
                raise ValueError("Research job results not found")

            with open(job.results_path, "r") as f:
                research_data = json.load(f)

            # Extract content for video
            script_content, script_title = await self._extract_video_content(
                research_data, job.source_type.value, custom_title
            )

            # Create video generation config
            config = VideoGenerationConfig(
                avatar_profile_id=avatar_profile_id or "default",
                aspect_ratio=aspect_ratio,
                voice_speed=voice_speed,
                enable_captions=True,
                title=script_title,
            )

            # Create video request
            request = ResearchVideoRequest(
                user_id=job.user_id,
                workspace_id=job.workspace_id,
                research_job_id=research_job_id,
                content_source=ContentSource.RESEARCH,
                source_tool=job.source_type.value,
                script_title=script_title,
                script_content=script_content,
                original_content=research_data,
                config=config,
            )

            # Generate video
            video_id = await avatar_video_service.create_video_from_research(request)

            logger.info(
                "Video creation initiated",
                video_id=video_id,
                research_job_id=research_job_id,
                script_length=len(script_content),
            )

            return video_id

        except Exception as e:
            logger.error("Failed to create video from research job", research_job_id=research_job_id, error=str(e))
            raise

    async def _extract_video_content(
        self, research_data: Dict[str, Any], source_tool: str, custom_title: Optional[str] = None
    ) -> Tuple[str, str]:
        """Extract video script content from research data"""

        try:
            rule = self.content_extraction_rules.get(source_tool)
            if not rule:
                # Generic extraction for unknown tools
                return await self._generic_content_extraction(research_data, source_tool, custom_title)

            # Extract content using specific rules
            extracted_content = []

            for content_path in rule.content_paths:
                content = self._extract_by_path(research_data, content_path)
                if content:
                    extracted_content.extend(self._format_content_items(content))

            if not extracted_content:
                # Fallback to generic extraction
                return await self._generic_content_extraction(research_data, source_tool, custom_title)

            # Format content for script
            formatted_content = self._format_extracted_content(extracted_content, rule)

            # Generate title
            topic = self._extract_topic_from_data(research_data, source_tool)
            title = custom_title or rule.title_template.format(topic=topic)

            # Generate script
            script = rule.script_template.format(content=formatted_content).strip()

            # Ensure length constraints
            if len(script) < rule.min_content_length:
                script = self._pad_script_content(script, rule.min_content_length)
            elif len(script) > rule.max_content_length:
                script = script[: rule.max_content_length] + "..."

            logger.info(
                "Content extracted successfully",
                source_tool=source_tool,
                script_length=len(script),
                content_items=len(extracted_content),
            )

            return script, title

        except Exception as e:
            logger.error("Failed to extract video content", source_tool=source_tool, error=str(e))
            # Fallback to generic extraction
            return await self._generic_content_extraction(research_data, source_tool, custom_title)

    def _extract_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """Extract data by JSON path"""
        try:
            keys = path.split(".")
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None

            return current

        except Exception:
            return None

    def _format_content_items(self, content: Any) -> List[str]:
        """Format content items into readable strings"""
        formatted = []

        if isinstance(content, list):
            for item in content[:5]:  # Limit to top 5 items
                if isinstance(item, dict):
                    # Extract key information from dict
                    if "title" in item and "description" in item:
                        formatted.append(f"{item['title']}: {item['description']}")
                    elif "query" in item and "growth" in item:
                        formatted.append(f"{item['query']} showing {item['growth']} growth")
                    elif "action" in item and "description" in item:
                        formatted.append(f"{item['action']} - {item['description']}")
                    elif "name" in item and "description" in item:
                        formatted.append(f"{item['name']}: {item['description']}")
                    else:
                        # Generic dict formatting
                        key_value_pairs = []
                        for k, v in item.items():
                            if isinstance(v, (str, int, float)) and len(str(v)) < 100:
                                key_value_pairs.append(f"{k}: {v}")
                        if key_value_pairs:
                            formatted.append(", ".join(key_value_pairs[:3]))
                elif isinstance(item, str):
                    formatted.append(item)
        elif isinstance(content, dict):
            # Handle single dict
            formatted.extend(self._format_content_items([content]))
        elif isinstance(content, str):
            formatted.append(content)

        return formatted

    def _format_extracted_content(self, content_items: List[str], rule: ContentExtractionRule) -> str:
        """Format extracted content items into readable script content"""
        if not content_items:
            return "Our research has revealed interesting insights and trends."

        # Format as numbered list for better readability
        formatted_items = []
        for i, item in enumerate(content_items[:5], 1):  # Limit to 5 items
            # Clean up the item text
            clean_item = item.strip()
            if not clean_item.endswith("."):
                clean_item += "."
            formatted_items.append(f"{i}. {clean_item}")

        return "\n\n".join(formatted_items)

    def _extract_topic_from_data(self, research_data: Dict[str, Any], source_tool: str) -> str:
        """Extract main topic from research data"""
        # Try to extract topic from various possible locations
        topic_paths = ["config.keywords", "config.search_terms", "config.topics", "metadata.topic", "query.keywords"]

        for path in topic_paths:
            topic_data = self._extract_by_path(research_data, path)
            if topic_data:
                if isinstance(topic_data, list) and topic_data:
                    return ", ".join(topic_data[:3])  # First 3 keywords
                elif isinstance(topic_data, str):
                    return topic_data

        # Fallback to source tool name
        return source_tool.replace("_", " ").title()

    def _pad_script_content(self, script: str, min_length: int) -> str:
        """Pad script content to meet minimum length"""
        if len(script) >= min_length:
            return script

        padding = """

        This analysis provides valuable insights for content creators, marketers, and businesses
        looking to stay ahead of trends and engage with their target audience effectively.
        By understanding these patterns and opportunities, we can make more informed decisions
        about content strategy and market positioning.
        """

        return script + padding.strip()

    async def _generic_content_extraction(
        self, research_data: Dict[str, Any], source_tool: str, custom_title: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generic content extraction for unknown research tools"""

        # Generate generic script
        source_name = source_tool.replace("_", " ").title()
        topic = self._extract_topic_from_data(research_data, source_tool)

        script = f"""
        Based on our latest {source_name} research analysis, we've uncovered valuable insights
        and emerging trends. Our comprehensive analysis of {topic} reveals key opportunities
        and patterns that are shaping the current landscape.

        The data shows significant developments that could impact content strategy,
        market positioning, and audience engagement. These findings provide actionable
        intelligence for making informed decisions and staying ahead of the curve.

        This research-driven approach helps identify emerging opportunities and understand
        the evolving dynamics in this space, enabling better strategic planning and execution.
        """.strip()

        title = custom_title or f"{source_name} Research Analysis - {topic}"

        return script, title

    async def process_completed_research_jobs(
        self, hours_back: int = 24, auto_create_videos: bool = False, avatar_profile_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Process recently completed research jobs for video creation"""

        try:
            # Get completed jobs from the last N hours
            since = datetime.now() - timedelta(hours=hours_back)

            # Get jobs from all research tools
            all_jobs = []
            for source_tool in self.content_extraction_rules.keys():
                jobs = await research_service.get_jobs_by_source(source_tool, since=since, status=JobStatus.COMPLETED)
                all_jobs.extend(jobs)

            logger.info("Found completed research jobs", count=len(all_jobs), hours_back=hours_back)

            results = []

            for job in all_jobs:
                try:
                    # Check if video already exists for this job
                    existing_videos = await avatar_video_service.get_user_videos(job.user_id, job.workspace_id)

                    job_has_video = any(video.get("research_job_id") == job.id for video in existing_videos)

                    if job_has_video:
                        logger.debug("Video already exists for research job", job_id=job.id)
                        continue

                    result = {
                        "job_id": job.id,
                        "user_id": job.user_id,
                        "workspace_id": job.workspace_id,
                        "source_tool": job.source_type.value,
                        "completed_at": job.completed_at,
                        "video_created": False,
                        "video_id": None,
                        "error": None,
                    }

                    if auto_create_videos:
                        try:
                            video_id = await self.create_video_from_research_job(
                                job.id, avatar_profile_id=avatar_profile_id
                            )

                            result["video_created"] = True
                            result["video_id"] = video_id

                            logger.info("Auto-created video from research job", job_id=job.id, video_id=video_id)

                        except Exception as e:
                            result["error"] = str(e)
                            logger.error("Failed to auto-create video", job_id=job.id, error=str(e))

                    results.append(result)

                except Exception as e:
                    logger.error("Error processing research job", job_id=job.id, error=str(e))

            return results

        except Exception as e:
            logger.error("Failed to process completed research jobs", error=str(e))
            return []

    async def create_video_campaign_from_research_config(
        self,
        research_config_id: str,
        campaign_name: str,
        avatar_profile_id: Optional[str] = None,
        frequency: str = "daily",
        max_videos_per_day: int = 3,
    ) -> str:
        """Create automated video campaign from research configuration"""

        try:
            # Get research configuration
            config = await research_service.get_configuration_by_id(research_config_id)
            if not config:
                raise ValueError(f"Research configuration not found: {research_config_id}")

            # Create video campaign
            campaign_config = {
                "name": campaign_name,
                "description": f"Automated video generation from {config.source_type.value} research",
                "research_config_id": research_config_id,
                "source_tools": [config.source_type.value],
                "profile_id": avatar_profile_id,
                "frequency": frequency,
                "max_videos_per_day": max_videos_per_day,
                "is_active": True,
                "auto_post_enabled": False,  # Can be enabled later
                "min_content_score": 70,
            }

            campaign_id = await avatar_video_service.create_automated_video_campaign(
                config.user_id, config.workspace_id, campaign_config
            )

            logger.info(
                "Video campaign created from research config",
                campaign_id=campaign_id,
                research_config_id=research_config_id,
            )

            return campaign_id

        except Exception as e:
            logger.error("Failed to create video campaign", research_config_id=research_config_id, error=str(e))
            raise


# Lazy initialization to avoid import-time environment variable issues
_research_to_video_integrator = None

def get_research_to_video_integrator():
    """Get research to video integrator with lazy initialization."""
    global _research_to_video_integrator
    if _research_to_video_integrator is None:
        _research_to_video_integrator = ResearchToVideoIntegrator()
    return _research_to_video_integrator


# Convenience functions
async def create_video_from_latest_research(
    user_id: str, source_tool: str = "google_trends", avatar_profile_id: Optional[str] = None
) -> Optional[str]:
    """Create video from user's latest research job"""

    try:
        # Get user's latest completed job for the source tool
        jobs = await research_service.get_user_jobs_by_source(user_id, source_tool, status=JobStatus.COMPLETED, limit=1)

        if not jobs:
            logger.warning("No completed research jobs found", user_id=user_id, source_tool=source_tool)
            return None

        latest_job = jobs[0]

        # Create video
        video_id = await research_to_video_integrator.create_video_from_research_job(
            latest_job.id, avatar_profile_id=avatar_profile_id
        )

        return video_id

    except Exception as e:
        logger.error(
            "Failed to create video from latest research", user_id=user_id, source_tool=source_tool, error=str(e)
        )
        return None


async def batch_create_videos_from_research(
    hours_back: int = 24, avatar_profile_id: Optional[str] = None
) -> Dict[str, Any]:
    """Batch create videos from recent research jobs"""

    results = await research_to_video_integrator.process_completed_research_jobs(
        hours_back=hours_back, auto_create_videos=True, avatar_profile_id=avatar_profile_id
    )

    summary = {
        "total_jobs_processed": len(results),
        "videos_created": len([r for r in results if r["video_created"]]),
        "errors": len([r for r in results if r["error"]]),
        "results": results,
    }

    logger.info("Batch video creation completed", **summary)
    return summary


if __name__ == "__main__":

    async def test_integration():
        """Test research to video integration"""
        try:
            # Test processing recent research jobs
            print("🔍 Processing recent research jobs...")
            results = await research_to_video_integrator.process_completed_research_jobs(
                hours_back=48, auto_create_videos=False  # Just analyze, don't create
            )

            print(f"✅ Found {len(results)} research jobs ready for video creation")

            for result in results[:3]:  # Show first 3
                print(f"   📊 {result['source_tool']} job from {result['completed_at']}")

            # Test creating video from specific job (if any exist)
            if results:
                print(f"\n🎬 Creating video from first research job...")
                video_id = await research_to_video_integrator.create_video_from_research_job(results[0]["job_id"])
                print(f"✅ Video creation started: {video_id}")

        except Exception as e:
            print(f"❌ Test failed: {e}")

    # Run test
    asyncio.run(test_integration())
