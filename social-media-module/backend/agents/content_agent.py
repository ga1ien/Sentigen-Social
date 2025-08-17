"""
Advanced content generation agent using Pydantic AI.
Supports multiple AI providers and platform-specific optimization.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from models.content import (
    AIProvider,
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentType,
    ContentVariation,
    Platform,
)
from utils.model_config import get_smart_model

logger = structlog.get_logger(__name__)


@dataclass
class ContentAgentDeps:
    """Dependencies for the content generation agent."""

    user_id: str
    workspace_id: str
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    brand_guidelines: Optional[Dict[str, Any]] = None
    platform_settings: Optional[Dict[Platform, Dict[str, Any]]] = None


class ContentGenerationResult(BaseModel):
    """Structured result from content generation."""

    variations: List[ContentVariation] = Field(..., description="Generated content variations")
    platform_optimizations: Dict[str, str] = Field(default_factory=dict, description="Platform-specific optimizations")
    hashtag_suggestions: List[str] = Field(default=[], description="Suggested hashtags")
    best_posting_times: Dict[str, str] = Field(default_factory=dict, description="Optimal posting times per platform")
    content_strategy_notes: str = Field(default="", description="Strategic notes about the content")
    estimated_engagement: Dict[str, float] = Field(default_factory=dict, description="Estimated engagement rates")


# System prompt for content generation
CONTENT_GENERATION_PROMPT = """
~~ CONTEXT: ~~
You are an expert social media content strategist and copywriter with deep knowledge of platform-specific best practices, audience psychology, and viral content patterns.

~~ GOAL: ~~
Generate high-quality, engaging social media content that is optimized for specific platforms and aligned with brand voice and audience preferences.

~~ PLATFORM EXPERTISE: ~~
- Twitter/X: Concise, witty, trending topics, hashtags, threads
- LinkedIn: Professional, thought leadership, industry insights, longer form
- Instagram: Visual-first, lifestyle, behind-the-scenes, stories
- Facebook: Community-focused, conversational, shareable
- TikTok: Trendy, entertaining, short-form, viral hooks
- YouTube: Educational, entertaining, storytelling

~~ CONTENT PRINCIPLES: ~~
- Hook readers in the first 3 words
- Use active voice and strong verbs
- Include emotional triggers when appropriate
- Optimize for platform algorithms
- Maintain brand consistency
- Consider accessibility and inclusivity

~~ OUTPUT REQUIREMENTS: ~~
- Generate multiple variations for A/B testing
- Provide platform-specific optimizations
- Include relevant hashtags and mentions
- Suggest optimal posting times
- Estimate engagement potential
- Provide strategic reasoning

~~ INSTRUCTIONS: ~~
- Analyze the prompt and target platforms carefully
- Consider brand voice and audience demographics
- Generate content that drives engagement and action
- Optimize character counts for each platform
- Include trending elements when relevant
- Provide actionable insights and recommendations
"""

# Create the content generation agent
content_agent = Agent(get_smart_model(), system_prompt=CONTENT_GENERATION_PROMPT, deps_type=ContentAgentDeps, retries=2)


@content_agent.system_prompt
def add_brand_context(ctx: RunContext[ContentAgentDeps]) -> str:
    """Add brand-specific context to the system prompt."""
    deps = ctx.deps
    context_parts = []

    if deps.brand_voice:
        context_parts.append(f"Brand Voice: {deps.brand_voice}")

    if deps.target_audience:
        context_parts.append(f"Target Audience: {deps.target_audience}")

    if deps.brand_guidelines:
        guidelines = json.dumps(deps.brand_guidelines, indent=2)
        context_parts.append(f"Brand Guidelines: {guidelines}")

    if context_parts:
        return f"\n\n~~ BRAND CONTEXT: ~~\n" + "\n".join(context_parts)

    return ""


@content_agent.system_prompt
def add_platform_context(ctx: RunContext[ContentAgentDeps]) -> str:
    """Add platform-specific context and settings."""
    deps = ctx.deps

    if deps.platform_settings:
        settings = json.dumps(deps.platform_settings, indent=2, default=str)
        return f"\n\n~~ PLATFORM SETTINGS: ~~\n{settings}"

    return ""


@content_agent.tool
async def analyze_trending_topics(
    ctx: RunContext[ContentAgentDeps], platforms: List[str], industry: Optional[str] = None
) -> str:
    """Analyze current trending topics for given platforms."""
    # In a real implementation, this would call trending APIs
    # For now, we'll return mock trending data

    trending_data = {
        "twitter": ["#MondayMotivation", "#TechTrends", "#AI", "#Productivity"],
        "linkedin": ["#Leadership", "#Innovation", "#RemoteWork", "#CareerGrowth"],
        "instagram": ["#BehindTheScenes", "#MondayMood", "#Inspiration", "#Lifestyle"],
        "tiktok": ["#Trending", "#ViralDance", "#LifeHacks", "#Comedy"],
        "facebook": ["#Community", "#Family", "#LocalBusiness", "#Events"],
    }

    result = {}
    for platform in platforms:
        if platform.lower() in trending_data:
            result[platform] = trending_data[platform.lower()]

    return json.dumps(result)


@content_agent.tool
async def get_optimal_posting_times(
    ctx: RunContext[ContentAgentDeps], platforms: List[str], timezone: str = "UTC"
) -> str:
    """Get optimal posting times for platforms based on audience data."""
    # Mock optimal posting times - in reality, this would use analytics data
    optimal_times = {
        "twitter": "9:00 AM, 1:00 PM, 5:00 PM",
        "linkedin": "8:00 AM, 12:00 PM, 5:00 PM (Tuesday-Thursday)",
        "instagram": "11:00 AM, 2:00 PM, 5:00 PM",
        "facebook": "9:00 AM, 1:00 PM, 3:00 PM",
        "tiktok": "6:00 AM, 10:00 AM, 7:00 PM",
        "youtube": "2:00 PM, 8:00 PM",
    }

    result = {}
    for platform in platforms:
        if platform.lower() in optimal_times:
            result[platform] = optimal_times[platform.lower()]

    return json.dumps(result)


@content_agent.tool
async def check_content_guidelines(ctx: RunContext[ContentAgentDeps], content: str, platforms: List[str]) -> str:
    """Check content against platform guidelines and brand standards."""
    # Mock content checking - in reality, this would use content moderation APIs
    guidelines_check = {
        "compliant": True,
        "warnings": [],
        "suggestions": [
            "Consider adding a call-to-action",
            "Include relevant hashtags for better discoverability",
            "Ensure accessibility with alt text for images",
        ],
        "character_counts": {"twitter": len(content), "linkedin": len(content), "instagram": len(content)},
    }

    return json.dumps(guidelines_check)


class ContentGenerationAgent:
    """Wrapper class for the content generation agent."""

    def __init__(self):
        self.agent = content_agent
        logger.info("Content generation agent initialized")

    async def generate_content(
        self,
        request: ContentGenerationRequest,
        user_id: str,
        workspace_id: str,
        brand_context: Optional[Dict[str, Any]] = None,
    ) -> ContentGenerationResponse:
        """
        Generate content based on the request parameters.

        Args:
            request: Content generation request
            user_id: User ID making the request
            workspace_id: Workspace ID
            brand_context: Optional brand context and settings

        Returns:
            ContentGenerationResponse with generated content
        """
        start_time = datetime.utcnow()

        try:
            # Prepare dependencies
            deps = ContentAgentDeps(
                user_id=user_id,
                workspace_id=workspace_id,
                brand_voice=brand_context.get("brand_voice") if brand_context else None,
                target_audience=brand_context.get("target_audience") if brand_context else None,
                brand_guidelines=brand_context.get("brand_guidelines") if brand_context else None,
                platform_settings=brand_context.get("platform_settings") if brand_context else None,
            )

            # Create the generation prompt
            platform_names = [p.value for p in request.platforms] if request.platforms else ["general"]
            generation_prompt = f"""
            Generate {request.content_type.value} content for the following platforms: {', '.join(platform_names)}

            Content Brief:
            - Prompt: {request.prompt}
            - Tone: {request.tone}
            - Length: {request.length}
            - Include hashtags: {request.include_hashtags}
            - Include emojis: {request.include_emojis}

            Additional Context: {request.additional_context or 'None provided'}

            Please generate 3-5 variations of the content, each optimized for the target platforms.
            Consider current trends, optimal posting times, and engagement strategies.
            """

            # Run the agent
            result = await self.agent.run(generation_prompt, deps=deps)

            # Calculate generation time
            end_time = datetime.utcnow()
            generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Extract the result data
            if hasattr(result, "data") and result.data:
                agent_result = result.data
            else:
                # Fallback parsing if structured result is not available
                agent_result = self._parse_fallback_result(result.output if hasattr(result, "output") else str(result))

            # Create response
            response = ContentGenerationResponse(
                variations=agent_result.variations,
                ai_provider=request.ai_provider,
                generation_time_ms=generation_time_ms,
                tokens_used=None,  # Would be populated by the actual AI provider
                cost_usd=None,  # Would be calculated based on provider pricing
            )

            logger.info(
                "Content generated successfully",
                user_id=user_id,
                workspace_id=workspace_id,
                variations_count=len(response.variations),
                generation_time_ms=generation_time_ms,
            )

            return response

        except Exception as e:
            logger.error("Content generation failed", user_id=user_id, workspace_id=workspace_id, error=str(e))
            raise

    def _parse_fallback_result(self, output: str) -> ContentGenerationResult:
        """Parse unstructured output as fallback."""
        # Simple fallback - create a single variation from the output
        variation = ContentVariation(
            content=output[:500] if len(output) > 500 else output,  # Truncate if too long
            character_count=len(output),
            hashtags=[],
            mentions=[],
        )

        return ContentGenerationResult(
            variations=[variation],
            platform_optimizations={},
            hashtag_suggestions=[],
            best_posting_times={},
            content_strategy_notes="Generated using fallback parsing",
            estimated_engagement={},
        )

    async def optimize_for_platform(self, content: str, platform: Platform, user_id: str, workspace_id: str) -> str:
        """
        Optimize existing content for a specific platform.

        Args:
            content: Original content
            platform: Target platform
            user_id: User ID
            workspace_id: Workspace ID

        Returns:
            Platform-optimized content
        """
        try:
            deps = ContentAgentDeps(user_id=user_id, workspace_id=workspace_id)

            optimization_prompt = f"""
            Optimize the following content specifically for {platform.value}:

            Original Content: {content}

            Please adapt this content to maximize engagement on {platform.value} while maintaining the core message.
            Consider platform-specific best practices, character limits, and audience expectations.
            """

            result = await self.agent.run(optimization_prompt, deps=deps)

            # Extract optimized content
            if hasattr(result, "data") and result.data:
                return result.data.variations[0].content if result.data.variations else content
            else:
                return result.output if hasattr(result, "output") else content

        except Exception as e:
            logger.error("Content optimization failed", platform=platform.value, error=str(e))
            return content  # Return original content if optimization fails
