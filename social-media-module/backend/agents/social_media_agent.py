"""
Pydantic AI agent for social media posting with Ayrshare integration.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from models.social_media import PostStatus, SupportedPlatform
from utils.ayrshare_client import AyrshareClient
from utils.heygen_client import HeyGenClient
from utils.model_config import get_smart_model

load_dotenv()

logger = structlog.get_logger(__name__)


@dataclass
class SocialMediaAgentDeps:
    """Dependencies required by the social media agent."""

    context: str
    ayrshare_client: AyrshareClient
    heygen_client: Optional[HeyGenClient] = None
    workspace_metadata: Optional[Dict[str, Any]] = None
    workspace_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class SocialMediaAgentResult:
    """Structured output from the social media agent."""

    status: str
    message: str
    post_id: Optional[str] = None
    ref_id: Optional[str] = None
    post_content: Optional[str] = None
    platform_results: List[Dict[str, Any]] = None
    errors: List[str] = None
    created_at: Optional[datetime] = None
    confidence_score: Optional[float] = None

    def __post_init__(self):
        if self.platform_results is None:
            self.platform_results = []
        if self.errors is None:
            self.errors = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


# Base system prompt
system_prompt = """
~~ CONTEXT: ~~
You are a specialized social media posting agent that helps users create and publish content across multiple social media platforms using the Ayrshare API. You have expertise in social media best practices, content optimization, and platform-specific requirements.

~~ GOAL: ~~
Your primary goal is to help users successfully post content to their connected social media accounts. You should optimize content for each platform, handle errors gracefully, and provide clear feedback about the posting results.

~~ STRUCTURE: ~~
Always return your response in the structured SocialMediaAgentResult format with:
- status: "success" or "error"
- message: Clear description of what happened
- post_id: Unique identifier if successful
- platform_results: Results for each platform
- errors: Any error messages
- post_content: The actual content that was posted

~~ INSTRUCTIONS: ~~
- Don't ask the user before taking an action, just do it
- Optimize content for each platform's character limits and best practices
- Handle platform-specific requirements (hashtags, mentions, media formats)
- Provide clear error messages and suggestions for fixes
- Use the available tools to interact with the Ayrshare API
- Be helpful and informative about social media posting best practices
"""

# Create agent with lazy model initialization
def get_social_media_agent():
    """Get the social media agent with lazy model initialization."""
    global _social_media_agent_instance
    if _social_media_agent_instance is None:
        _social_media_agent_instance = Agent(
            get_smart_model(),
            system_prompt=system_prompt,
            deps_type=SocialMediaAgentDeps,
            instructions="You are an expert in social media posting and the current date is {current_date}.",
            retries=2,
        )

        # Add the system prompt decorator
        @_social_media_agent_instance.system_prompt
        def add_context(ctx: RunContext[SocialMediaAgentDeps]) -> str:
    """Add dynamic context to the system prompt."""
    deps = ctx.deps
    return f"""
    \n\nAdditional context for social media posting:
    {deps.context}

    Available platforms and posting capabilities will be determined by the user's connected accounts.
    """


@social_media_agent.instructions
def add_workspace_instructions(ctx: RunContext[SocialMediaAgentDeps]) -> str:
    """Add workspace-specific instructions."""
    if ctx.deps.workspace_metadata:
        return f"The workspace instructions are {ctx.deps.workspace_metadata.get('instructions', 'N/A')}."
    return ""


@social_media_agent.instructions
def add_workspace_description(ctx: RunContext[SocialMediaAgentDeps]) -> str:
    """Add workspace description context."""
    if ctx.deps.workspace_metadata:
        return f"The workspace description is {ctx.deps.workspace_metadata.get('description', 'N/A')}."
    return ""


@social_media_agent.tool
async def post_to_social_media(
    ctx: RunContext[SocialMediaAgentDeps],
    post_content: Optional[str] = None,
    platforms: List[str] = None,
    media_urls: Optional[List[str]] = None,
    schedule_date: Optional[str] = None,
    random_post: bool = False,
    random_media_url: bool = False,
    is_landscape_video: bool = False,
    is_portrait_video: bool = False,
    hashtags: Optional[List[str]] = None,
    mentions: Optional[List[str]] = None,
    platform_options: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Post content to social media platforms using Ayrshare API.

    Args:
        ctx: The context object
        post_content: The text content to post
        platforms: List of platform names (twitter, facebook, instagram, linkedin, etc.)
        media_urls: List of image/video URLs to include
        schedule_date: ISO format date string for scheduling
        random_post: Use random content for testing
        random_media_url: Use random media for testing
        is_landscape_video: Use landscape video format
        is_portrait_video: Use portrait video format (required for TikTok/Reels)
        hashtags: List of hashtags to include
        mentions: List of usernames to mention
        platform_options: Platform-specific posting options

    Returns:
        str: JSON string containing the posting results
    """
    logger.info("Social media agent posting", platforms=platforms, has_content=bool(post_content))

    try:
        # Validate inputs
        if not platforms:
            return '{"status": "error", "message": "At least one platform must be specified", "errors": ["No platforms provided"]}'

        if not post_content and not random_post:
            return '{"status": "error", "message": "Either post content or random_post must be provided", "errors": ["No content provided"]}'

        # Process hashtags and mentions into content if provided
        final_content = post_content
        if final_content and (hashtags or mentions):
            if hashtags:
                hashtag_str = " " + " ".join(hashtags)
                final_content += hashtag_str
            if mentions:
                mention_str = " " + " ".join(mentions)
                final_content += mention_str

        # Parse schedule date if provided
        parsed_schedule_date = None
        if schedule_date:
            try:
                parsed_schedule_date = datetime.fromisoformat(schedule_date.replace("Z", "+00:00"))
            except ValueError:
                return f'{{"status": "error", "message": "Invalid schedule date format: {schedule_date}", "errors": ["Invalid date format"]}}'

        # Make the API call
        result = await ctx.deps.ayrshare_client.post_to_social_media(
            post_content=final_content,
            platforms=platforms,
            media_urls=media_urls,
            schedule_date=parsed_schedule_date,
            random_post=random_post,
            random_media_url=random_media_url,
            is_landscape_video=is_landscape_video,
            is_portrait_video=is_portrait_video,
            platform_options=platform_options,
        )

        logger.info("Social media post successful", result_status=result.get("status"))

        # Return the result as JSON string
        import json

        return json.dumps(result)

    except Exception as e:
        error_msg = str(e)
        logger.error("Social media posting failed", error=error_msg)

        import json

        return json.dumps(
            {
                "status": "error",
                "message": f"Failed to post to social media: {error_msg}",
                "errors": [error_msg],
                "platform_results": [],
            }
        )


@social_media_agent.tool
async def get_connected_accounts(ctx: RunContext[SocialMediaAgentDeps]) -> str:
    """
    Get the list of connected social media accounts.

    Args:
        ctx: The context object

    Returns:
        str: JSON string containing connected accounts information
    """
    logger.info("Getting connected social media accounts")

    try:
        result = await ctx.deps.ayrshare_client.get_connected_accounts()

        import json

        return json.dumps(result)

    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to get connected accounts", error=error_msg)

        import json

        return json.dumps(
            {"status": "error", "message": f"Failed to get connected accounts: {error_msg}", "errors": [error_msg]}
        )


@social_media_agent.tool
async def get_post_analytics(ctx: RunContext[SocialMediaAgentDeps], post_id: str) -> str:
    """
    Get analytics for a specific social media post.

    Args:
        ctx: The context object
        post_id: The ID of the post to get analytics for

    Returns:
        str: JSON string containing analytics data
    """
    logger.info("Getting post analytics", post_id=post_id)

    try:
        result = await ctx.deps.ayrshare_client.get_post_analytics(post_id)

        import json

        return json.dumps(result)

    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to get post analytics", error=error_msg, post_id=post_id)

        import json

        return json.dumps(
            {"status": "error", "message": f"Failed to get post analytics: {error_msg}", "errors": [error_msg]}
        )


@social_media_agent.tool
async def optimize_content_for_platforms(
    ctx: RunContext[SocialMediaAgentDeps],
    content: str,
    platforms: List[str],
    include_hashtags: bool = True,
    include_mentions: bool = True,
) -> str:
    """
    Optimize content for specific social media platforms.

    Args:
        ctx: The context object
        content: The original content to optimize
        platforms: List of platforms to optimize for
        include_hashtags: Whether to suggest hashtags
        include_mentions: Whether to include mentions

    Returns:
        str: JSON string with optimized content suggestions for each platform
    """
    logger.info("Optimizing content for platforms", platforms=platforms)

    try:
        # Platform-specific optimization rules
        optimizations = {}

        for platform in platforms:
            platform_lower = platform.lower()
            optimized = content
            suggestions = []

            if platform_lower == "twitter":
                # Twitter has 280 character limit
                if len(content) > 280:
                    optimized = content[:277] + "..."
                    suggestions.append("Content truncated to fit Twitter's 280 character limit")
                if include_hashtags:
                    suggestions.append("Consider adding 1-2 relevant hashtags")

            elif platform_lower == "instagram":
                # Instagram allows longer content and loves hashtags
                if include_hashtags:
                    suggestions.append("Instagram performs well with 5-10 hashtags")
                suggestions.append("Consider adding an engaging visual")

            elif platform_lower == "linkedin":
                # LinkedIn is professional
                suggestions.append("Keep tone professional and industry-focused")
                if include_hashtags:
                    suggestions.append("Use 3-5 professional hashtags")

            elif platform_lower == "facebook":
                # Facebook allows long content
                suggestions.append("Facebook posts can be longer and more conversational")

            elif platform_lower == "tiktok":
                # TikTok is video-focused
                suggestions.append("TikTok requires video content - consider portrait format")
                if include_hashtags:
                    suggestions.append("Use trending hashtags for better reach")

            optimizations[platform] = {
                "optimized_content": optimized,
                "suggestions": suggestions,
                "character_count": len(optimized),
            }

        import json

        return json.dumps({"status": "success", "optimizations": optimizations})

    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to optimize content", error=error_msg)

        import json

        return json.dumps(
            {"status": "error", "message": f"Failed to optimize content: {error_msg}", "errors": [error_msg]}
        )


@social_media_agent.tool
async def generate_video_with_heygen(
    ctx: RunContext[SocialMediaAgentDeps],
    script: str,
    avatar_id: Optional[str] = None,
    voice_id: Optional[str] = None,
    background: Optional[str] = None,
) -> str:
    """
    Generate a video using HeyGen API.

    Args:
        ctx: The context object
        script: The text script for the video
        avatar_id: ID of the avatar to use (optional)
        voice_id: ID of the voice to use (optional)
        background: Background setting (optional)

    Returns:
        str: JSON string containing video generation results
    """
    logger.info("Generating HeyGen video", script_length=len(script))

    try:
        if not ctx.deps.heygen_client:
            return json.dumps(
                {
                    "status": "error",
                    "message": "HeyGen client not available. Please configure HEYGEN_API_KEY.",
                    "errors": ["HeyGen client not initialized"],
                }
            )

        result = await ctx.deps.heygen_client.create_video(
            script=script, avatar_id=avatar_id, voice_id=voice_id, background=background
        )

        logger.info("HeyGen video generation successful", video_id=result.get("video_id"))

        import json

        return json.dumps(result)

    except Exception as e:
        error_msg = str(e)
        logger.error("HeyGen video generation failed", error=error_msg)

        import json

        return json.dumps(
            {"status": "error", "message": f"Failed to generate video: {error_msg}", "errors": [error_msg]}
        )


@social_media_agent.tool
async def get_heygen_video_status(ctx: RunContext[SocialMediaAgentDeps], video_id: str) -> str:
    """
    Get the status of a HeyGen video generation.

    Args:
        ctx: The context object
        video_id: The video ID to check

    Returns:
        str: JSON string containing video status
    """
    logger.info("Getting HeyGen video status", video_id=video_id)

    try:
        if not ctx.deps.heygen_client:
            return json.dumps(
                {
                    "status": "error",
                    "message": "HeyGen client not available",
                    "errors": ["HeyGen client not initialized"],
                }
            )

        result = await ctx.deps.heygen_client.get_video_status(video_id)

        import json

        return json.dumps(result)

    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to get HeyGen video status", error=error_msg, video_id=video_id)

        import json

        return json.dumps(
            {"status": "error", "message": f"Failed to get video status: {error_msg}", "errors": [error_msg]}
        )


@social_media_agent.tool
async def list_heygen_avatars(ctx: RunContext[SocialMediaAgentDeps]) -> str:
    """
    Get list of available HeyGen avatars.

    Args:
        ctx: The context object

    Returns:
        str: JSON string containing available avatars
    """
    logger.info("Getting HeyGen avatars list")

    try:
        if not ctx.deps.heygen_client:
            return json.dumps(
                {
                    "status": "error",
                    "message": "HeyGen client not available",
                    "errors": ["HeyGen client not initialized"],
                }
            )

        result = await ctx.deps.heygen_client.list_avatars()

        import json

        return json.dumps(result)

    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to get HeyGen avatars", error=error_msg)

        import json

        return json.dumps({"status": "error", "message": f"Failed to get avatars: {error_msg}", "errors": [error_msg]})


# Convenience class for easier usage
class SocialMediaAgent:
    """Wrapper class for the social media agent."""

    def __init__(self, ayrshare_api_key: Optional[str] = None, heygen_api_key: Optional[str] = None):
        """
        Initialize the social media agent.

        Args:
            ayrshare_api_key: Ayrshare API key. If None, uses environment variable.
            heygen_api_key: HeyGen API key. If None, uses environment variable.
        """
        self.ayrshare_client = AyrshareClient(api_key=ayrshare_api_key)

        # Initialize HeyGen client if API key is available
        try:
            self.heygen_client = HeyGenClient(api_key=heygen_api_key)
        except ValueError:
            # HeyGen API key not provided, client will be None
            self.heygen_client = None
            logger.info("HeyGen client not initialized - API key not provided")

    async def post_content(
        self,
        prompt: str,
        context: str = "You are helping a user post content to social media.",
        workspace_metadata: Optional[Dict[str, Any]] = None,
    ) -> SocialMediaAgentResult:
        """
        Use the agent to post content to social media.

        Args:
            prompt: The user's request/prompt
            context: Additional context for the agent
            workspace_metadata: Workspace-specific metadata

        Returns:
            SocialMediaAgentResult with the posting results
        """
        deps = SocialMediaAgentDeps(
            context=context,
            ayrshare_client=self.ayrshare_client,
            heygen_client=self.heygen_client,
            workspace_metadata=workspace_metadata or {},
        )

        try:
            result = await social_media_agent.run(prompt, deps=deps)

            # Extract structured result
            if hasattr(result, "data"):
                return result.data
            else:
                # Handle fallback cases - create result from output
                return SocialMediaAgentResult(
                    status="success", message="Content processed successfully", post_content=str(result.output)
                )

        except Exception as e:
            logger.error(f"Social media agent error: {str(e)}")
            return SocialMediaAgentResult(status="error", message=f"Agent error: {str(e)}", errors=[str(e)])


# Example usage function
async def main():
    """Example of running the social media agent."""
    # Example prompt for the agent
    prompt = """
    Please post the following content to Twitter and LinkedIn:

    "Excited to share our latest AI breakthrough! Our new social media automation tool is now live. 🚀 #AI #SocialMedia #Innovation"

    Also include the image: https://img.ayrshare.com/012/gb.jpg
    """

    # Create dependencies with context
    ayrshare_client = AyrshareClient()
    deps = SocialMediaAgentDeps(
        context="You are helping a user post content about their AI product launch.",
        ayrshare_client=ayrshare_client,
        workspace_metadata={
            "instructions": "Focus on professional tone for business content",
            "description": "AI product marketing workspace",
        },
    )

    # Run the agent
    response = await social_media_agent.run(prompt, deps=deps)

    # Print the response
    print("Agent Response:")
    print(response.output)

    # Access structured data if available
    if hasattr(response, "data"):
        structured_result = response.data
        print(f"Status: {structured_result.status}")
        print(f"Message: {structured_result.message}")
        print(f"Post ID: {structured_result.post_id}")
        print(f"Platform Results: {structured_result.platform_results}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
