"""
Content Worker using Claude 4 Sonnet for main chat and social media content drafting.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

from workers.base_worker import BaseWorker, WorkerTask, WorkerResult
from utils.model_config import get_smart_model

load_dotenv()

logger = structlog.get_logger(__name__)


@dataclass
class ContentWorkerDeps:
    """Dependencies for the content worker."""
    context: str
    research_data: Optional[Dict[str, Any]] = None
    brand_guidelines: Optional[Dict[str, Any]] = None
    target_audience: Optional[Dict[str, Any]] = None
    platform_specs: Optional[Dict[str, Any]] = None


class ContentWorker(BaseWorker):
    """Worker specialized for content creation and social media drafting using Claude 4 Sonnet."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("content_worker", config)
        self._initialize_agent()
    
    def _initialize_config(self):
        """Initialize Claude 4 Sonnet specific configuration."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-4-sonnet")
        
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found - content worker will be disabled")
            return
        
        self.config.update({
            "api_key": self.api_key,
            "model": self.model
        })
    
    def _initialize_agent(self):
        """Initialize the Claude 4 Sonnet agent for content creation."""
        if not self.api_key:
            self.agent = None
            return
        
        # Set environment variables for the model configuration
        os.environ["LLM_PROVIDER"] = "anthropic"
        os.environ["ANTHROPIC_API_KEY"] = self.api_key
        os.environ["ANTHROPIC_MODEL"] = self.model
        
        system_prompt = """
        ~~ CONTEXT: ~~
        You are an expert social media content creator and copywriter specializing in creating engaging, platform-optimized content. You have deep knowledge of social media trends, audience psychology, and content strategy across all major platforms.

        ~~ GOAL: ~~
        Create compelling, engaging social media content that drives engagement, builds brand awareness, and connects with target audiences. Optimize content for specific platforms and audiences.

        ~~ CAPABILITIES: ~~
        - Draft social media posts for all major platforms
        - Create content series and campaigns
        - Optimize content for engagement and reach
        - Adapt tone and style for different audiences
        - Incorporate trending topics and hashtags
        - Create compelling captions and copy
        - Develop content strategies

        ~~ INSTRUCTIONS: ~~
        - Always consider the target platform's best practices
        - Optimize for engagement and shareability
        - Use appropriate tone and voice for the brand
        - Include relevant hashtags and mentions when appropriate
        - Consider visual content recommendations
        - Provide multiple variations when requested
        - Be creative and authentic
        """
        
        try:
            self.agent = Agent(
                get_smart_model(),
                system_prompt=system_prompt,
                deps_type=ContentWorkerDeps,
                instructions="You are an expert content creator. The current date is {current_date}.",
                retries=2
            )
            
            logger.info("Content worker agent initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize content worker agent", error=str(e))
            self.agent = None
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process a content creation task using Claude 4 Sonnet.
        
        Args:
            task: Content creation task
            
        Returns:
            WorkerResult with generated content
        """
        if not self.agent:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="Claude 4 Sonnet agent not initialized"
            )
        
        try:
            # Extract task parameters
            content_type = task.input_data.get("content_type", "social_post")
            prompt = task.input_data.get("prompt", "")
            platform = task.input_data.get("platform", "general")
            research_data = task.input_data.get("research_data")
            brand_guidelines = task.input_data.get("brand_guidelines")
            target_audience = task.input_data.get("target_audience")
            
            if not prompt:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message="No prompt provided for content creation"
                )
            
            # Create dependencies
            deps = ContentWorkerDeps(
                context=f"Creating {content_type} for {platform}",
                research_data=research_data,
                brand_guidelines=brand_guidelines,
                target_audience=target_audience,
                platform_specs=self._get_platform_specs(platform)
            )
            
            # Build the content creation prompt
            full_prompt = self._build_content_prompt(
                content_type, prompt, platform, research_data, brand_guidelines, target_audience
            )
            
            # Run the agent
            result = await self.agent.run(full_prompt, deps=deps)
            
            # Extract the generated content
            if hasattr(result, 'data') and result.data:
                content_result = result.data
            else:
                content_result = str(result.output)
            
            content_data = {
                "content_type": content_type,
                "platform": platform,
                "generated_content": content_result,
                "prompt": prompt,
                "model_used": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Content creation task completed successfully",
                task_id=task.task_id,
                content_type=content_type,
                platform=platform,
                content_length=len(str(content_result))
            )
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="success",
                result=content_data,
                metadata={
                    "model": self.model,
                    "content_type": content_type,
                    "platform": platform,
                    "content_length": len(str(content_result))
                }
            )
            
        except Exception as e:
            logger.error("Content creation task failed", task_id=task.task_id, error=str(e))
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Content creation failed: {str(e)}"
            )
    
    def _build_content_prompt(
        self, 
        content_type: str, 
        prompt: str, 
        platform: str,
        research_data: Optional[Dict[str, Any]] = None,
        brand_guidelines: Optional[Dict[str, Any]] = None,
        target_audience: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a comprehensive content creation prompt."""
        
        prompt_parts = [f"Create {content_type} for {platform}:"]
        prompt_parts.append(f"\nContent Request: {prompt}")
        
        if research_data:
            prompt_parts.append(f"\nResearch Context: {research_data.get('findings', '')}")
        
        if brand_guidelines:
            prompt_parts.append(f"\nBrand Guidelines:")
            prompt_parts.append(f"- Tone: {brand_guidelines.get('tone', 'professional')}")
            prompt_parts.append(f"- Voice: {brand_guidelines.get('voice', 'friendly')}")
            prompt_parts.append(f"- Style: {brand_guidelines.get('style', 'engaging')}")
        
        if target_audience:
            prompt_parts.append(f"\nTarget Audience:")
            prompt_parts.append(f"- Demographics: {target_audience.get('demographics', 'general')}")
            prompt_parts.append(f"- Interests: {target_audience.get('interests', 'varied')}")
            prompt_parts.append(f"- Behavior: {target_audience.get('behavior', 'active social media users')}")
        
        # Add platform-specific instructions
        platform_instructions = self._get_platform_instructions(platform)
        if platform_instructions:
            prompt_parts.append(f"\nPlatform-Specific Requirements:\n{platform_instructions}")
        
        prompt_parts.append("\nPlease provide engaging, optimized content that follows best practices for the platform.")
        
        return "\n".join(prompt_parts)
    
    def _get_platform_specs(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific specifications."""
        specs = {
            "twitter": {
                "max_length": 280,
                "hashtag_limit": 2,
                "best_practices": ["concise", "engaging", "use_threads_for_longer_content"]
            },
            "instagram": {
                "max_length": 2200,
                "hashtag_limit": 30,
                "best_practices": ["visual_focused", "storytelling", "use_hashtags_strategically"]
            },
            "linkedin": {
                "max_length": 3000,
                "hashtag_limit": 5,
                "best_practices": ["professional_tone", "industry_insights", "thought_leadership"]
            },
            "facebook": {
                "max_length": 63206,
                "hashtag_limit": 5,
                "best_practices": ["conversational", "community_building", "shareable_content"]
            },
            "tiktok": {
                "max_length": 2200,
                "hashtag_limit": 10,
                "best_practices": ["trendy", "entertaining", "video_focused"]
            }
        }
        
        return specs.get(platform.lower(), {
            "max_length": 2200,
            "hashtag_limit": 10,
            "best_practices": ["engaging", "authentic", "platform_appropriate"]
        })
    
    def _get_platform_instructions(self, platform: str) -> str:
        """Get platform-specific content instructions."""
        instructions = {
            "twitter": "Keep it concise and punchy. Use 1-2 relevant hashtags. Consider thread potential for longer ideas.",
            "instagram": "Focus on visual storytelling. Use up to 30 hashtags strategically. Include a compelling caption that encourages engagement.",
            "linkedin": "Maintain a professional tone. Share industry insights or thought leadership. Use 3-5 professional hashtags.",
            "facebook": "Be conversational and community-focused. Encourage comments and shares. Keep hashtags minimal (1-3).",
            "tiktok": "Be trendy and entertaining. Use popular hashtags and sounds. Focus on video content ideas.",
            "bluesky": "Similar to Twitter but with a more relaxed tone. Focus on authentic conversations.",
            "pinterest": "Create descriptive, keyword-rich content. Focus on visual appeal and searchability."
        }
        
        return instructions.get(platform.lower(), "Create engaging, platform-appropriate content that resonates with the audience.")
    
    async def health_check(self) -> bool:
        """Check if Claude 4 Sonnet agent is working."""
        if not self.agent:
            self.is_healthy = False
            return False
        
        try:
            # Simple test task
            test_deps = ContentWorkerDeps(context="Health check test")
            result = await self.agent.run("Say hello", deps=test_deps)
            
            self.is_healthy = bool(result)
            self.last_health_check = datetime.utcnow()
            
            return self.is_healthy
            
        except Exception as e:
            logger.warning("Content worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False
    
    async def create_social_post(
        self, 
        prompt: str, 
        platform: str,
        research_data: Optional[Dict[str, Any]] = None,
        brand_guidelines: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a social media post for a specific platform.
        
        Args:
            prompt: Content creation prompt
            platform: Target platform
            research_data: Optional research context
            brand_guidelines: Optional brand guidelines
            
        Returns:
            Generated content or None if failed
        """
        task = WorkerTask(
            task_id=f"social_post_{platform}_{datetime.utcnow().timestamp()}",
            task_type="social_post",
            input_data={
                "content_type": "social_post",
                "prompt": prompt,
                "platform": platform,
                "research_data": research_data,
                "brand_guidelines": brand_guidelines
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def create_content_series(
        self, 
        topic: str, 
        platforms: List[str],
        post_count: int = 5,
        research_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a series of related content for multiple platforms.
        
        Args:
            topic: Main topic for the content series
            platforms: List of target platforms
            post_count: Number of posts to create
            research_data: Optional research context
            
        Returns:
            Generated content series or None if failed
        """
        task = WorkerTask(
            task_id=f"content_series_{topic}_{datetime.utcnow().timestamp()}",
            task_type="content_series",
            input_data={
                "content_type": "content_series",
                "prompt": f"Create a {post_count}-part content series about {topic}",
                "platform": "multi_platform",
                "platforms": platforms,
                "post_count": post_count,
                "research_data": research_data
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None