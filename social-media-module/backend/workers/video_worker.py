"""
Video Worker using Google Veo3 for advanced video generation.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from dotenv import load_dotenv
import httpx
from google.auth import default
from google.auth.transport.requests import Request

from workers.base_worker import BaseWorker, WorkerTask, WorkerResult

load_dotenv()

logger = structlog.get_logger(__name__)


class VideoWorker(BaseWorker):
    """Worker specialized for video generation using Google Veo3."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("video_worker", config)
    
    def _initialize_config(self):
        """Initialize Google Veo3 via Gemini API configuration."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
        self.model = os.getenv("GOOGLE_VEO3_MODEL", "gemini-2.0-flash-exp")
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found - video worker will be disabled")
            return
        
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        self.config.update({
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model
        })
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process a video generation task using Google Veo3.
        
        Args:
            task: Video generation task
            
        Returns:
            WorkerResult with video generation data
        """
        if not self.api_key:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="Gemini API key not configured for Veo3 access"
            )
        
        try:
            # Extract task parameters
            prompt = task.input_data.get("prompt", "")
            duration = task.input_data.get("duration", 5)  # seconds
            aspect_ratio = task.input_data.get("aspect_ratio", "16:9")
            style = task.input_data.get("style", "realistic")
            motion_level = task.input_data.get("motion_level", "medium")
            quality = task.input_data.get("quality", "standard")
            
            if not prompt:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message="No prompt provided for video generation"
                )
            
            # Enhance prompt based on style and requirements
            enhanced_prompt = self._enhance_video_prompt(prompt, style, motion_level)
            
            # Prepare API request for Veo3 via Gemini API
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Generate a video: {enhanced_prompt}"
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 8192,
                    "temperature": 0.7,
                    "topP": 0.8,
                    "topK": 40
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            # Make API call to Gemini API for Veo3
            async with httpx.AsyncClient(timeout=300.0) as client:  # Long timeout for video generation
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result_data = response.json()
                
                # Process video generation result
                video_result = {
                    "prompt": prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                    "style": style,
                    "motion_level": motion_level,
                    "quality": quality,
                    "video_id": result_data.get("video_id"),
                    "status": result_data.get("status", "processing"),
                    "video_url": result_data.get("video_url"),
                    "thumbnail_url": result_data.get("thumbnail_url"),
                    "estimated_completion": result_data.get("estimated_completion"),
                    "generation_params": payload,
                    "timestamp": datetime.utcnow().isoformat(),
                    "veo3_response": result_data
                }
                
                logger.info(
                    "Video generation task completed successfully",
                    task_id=task.task_id,
                    video_id=result_data.get("video_id"),
                    duration=duration,
                    style=style
                )
                
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="success",
                    result=video_result,
                    metadata={
                        "video_id": result_data.get("video_id"),
                        "duration": duration,
                        "style": style,
                        "aspect_ratio": aspect_ratio
                    }
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = f"Google Veo3 API error: {e.response.status_code}"
            try:
                error_response = e.response.json()
                error_detail += f" - {error_response.get('error', {}).get('message', str(e))}"
            except:
                error_detail += f" - {str(e)}"
            
            logger.error("Video generation task failed", task_id=task.task_id, error=error_detail)
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=error_detail
            )
            
        except Exception as e:
            logger.error("Unexpected error in video generation task", task_id=task.task_id, error=str(e))
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Video generation failed: {str(e)}"
            )
    
    def _enhance_video_prompt(self, prompt: str, style: str, motion_level: str) -> str:
        """Enhance the video prompt based on style and motion requirements."""
        style_enhancements = {
            "realistic": "photorealistic, high-quality, natural lighting, cinematic",
            "animated": "animated style, smooth animation, colorful, engaging",
            "artistic": "artistic style, creative, stylized, beautiful composition",
            "documentary": "documentary style, professional, informative, clear",
            "commercial": "commercial quality, professional, marketing-ready, polished",
            "social_media": "social media optimized, engaging, eye-catching, trendy",
            "educational": "educational content, clear, informative, professional",
            "entertainment": "entertaining, dynamic, engaging, fun"
        }
        
        motion_enhancements = {
            "low": "subtle movement, gentle motion, calm",
            "medium": "moderate movement, balanced motion, smooth transitions",
            "high": "dynamic movement, energetic, fast-paced, action-packed"
        }
        
        style_enhancement = style_enhancements.get(style, style_enhancements["realistic"])
        motion_enhancement = motion_enhancements.get(motion_level, motion_enhancements["medium"])
        
        enhanced_prompt = f"{prompt}, {style_enhancement}, {motion_enhancement}"
        
        return enhanced_prompt
    
    async def health_check(self) -> bool:
        """Check if Gemini API is accessible for Veo3."""
        if not self.api_key:
            self.is_healthy = False
            return False
        
        try:
            # Simple test request to check API availability
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/models/{self.model}",
                    headers=self.headers
                )
                
                self.is_healthy = response.status_code == 200
                self.last_health_check = datetime.utcnow()
                
                return self.is_healthy
                
        except Exception as e:
            logger.warning("Video worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False
    
    async def get_video_status(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a video generation.
        
        Args:
            video_id: Google Veo3 video ID
            
        Returns:
            Video status information or None if failed
        """
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/videos/{video_id}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error("Failed to get video status", video_id=video_id, error=str(e))
            return None
    
    async def generate_social_media_video(
        self, 
        prompt: str, 
        platform: str = "general",
        duration: int = 15
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a video optimized for social media platforms.
        
        Args:
            prompt: Video generation prompt
            platform: Target social media platform
            duration: Video duration in seconds
            
        Returns:
            Generated video data or None if failed
        """
        # Platform-specific optimization
        platform_configs = {
            "instagram": {"aspect_ratio": "9:16", "style": "social_media", "duration": min(duration, 60)},
            "instagram_story": {"aspect_ratio": "9:16", "style": "social_media", "duration": min(duration, 15)},
            "instagram_reel": {"aspect_ratio": "9:16", "style": "entertainment", "duration": min(duration, 90)},
            "tiktok": {"aspect_ratio": "9:16", "style": "entertainment", "duration": min(duration, 60)},
            "youtube": {"aspect_ratio": "16:9", "style": "realistic", "duration": min(duration, 300)},
            "youtube_shorts": {"aspect_ratio": "9:16", "style": "entertainment", "duration": min(duration, 60)},
            "twitter": {"aspect_ratio": "16:9", "style": "social_media", "duration": min(duration, 140)},
            "linkedin": {"aspect_ratio": "16:9", "style": "commercial", "duration": min(duration, 180)},
            "facebook": {"aspect_ratio": "16:9", "style": "social_media", "duration": min(duration, 240)},
            "general": {"aspect_ratio": "16:9", "style": "realistic", "duration": duration}
        }
        
        config = platform_configs.get(platform.lower(), platform_configs["general"])
        
        # Enhance prompt for social media
        social_prompt = f"{prompt}, optimized for {platform}, engaging, high-quality"
        
        task = WorkerTask(
            task_id=f"social_video_{platform}_{datetime.utcnow().timestamp()}",
            task_type="social_media_video",
            input_data={
                "prompt": social_prompt,
                "duration": config["duration"],
                "aspect_ratio": config["aspect_ratio"],
                "style": config["style"],
                "motion_level": "medium",
                "quality": "high"
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def generate_branded_video(
        self, 
        prompt: str, 
        brand_guidelines: Optional[Dict[str, Any]] = None,
        duration: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a branded video.
        
        Args:
            prompt: Video generation prompt
            brand_guidelines: Brand guidelines for video styling
            duration: Video duration in seconds
            
        Returns:
            Generated branded video data or None if failed
        """
        # Apply brand guidelines
        style = "commercial"
        motion_level = "medium"
        
        if brand_guidelines:
            brand_style = brand_guidelines.get("video_style", "commercial")
            brand_tone = brand_guidelines.get("tone", "professional")
            
            if brand_tone == "energetic":
                motion_level = "high"
            elif brand_tone == "calm":
                motion_level = "low"
            
            style = brand_style
        
        # Enhance prompt with brand context
        brand_prompt = prompt
        if brand_guidelines and brand_guidelines.get("brand_colors"):
            colors = brand_guidelines["brand_colors"]
            brand_prompt += f", incorporating brand colors: {', '.join(colors)}"
        
        task = WorkerTask(
            task_id=f"branded_video_{datetime.utcnow().timestamp()}",
            task_type="branded_video",
            input_data={
                "prompt": brand_prompt,
                "duration": min(duration, 120),
                "aspect_ratio": "16:9",
                "style": style,
                "motion_level": motion_level,
                "quality": "high"
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def generate_video_series(
        self, 
        prompts: List[str], 
        style: str = "realistic",
        duration: int = 15
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Generate a series of related videos.
        
        Args:
            prompts: List of video prompts
            style: Video style for all videos
            duration: Duration for each video
            
        Returns:
            List of generated video data or None if failed
        """
        tasks = []
        for i, prompt in enumerate(prompts):
            task = WorkerTask(
                task_id=f"video_series_{i}_{datetime.utcnow().timestamp()}",
                task_type="video_series",
                input_data={
                    "prompt": f"{prompt}, part {i+1} of series",
                    "duration": duration,
                    "aspect_ratio": "16:9",
                    "style": style,
                    "motion_level": "medium",
                    "quality": "high"
                }
            )
            tasks.append(task)
        
        # Process videos concurrently
        results = await self.batch_process(tasks)
        
        successful_results = [
            result.result for result in results 
            if result.status == "success"
        ]
        
        return successful_results if successful_results else None