"""
Avatar Video Worker using HeyGen for generating avatar-based videos.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from dotenv import load_dotenv

from workers.base_worker import BaseWorker, WorkerTask, WorkerResult
from utils.heygen_client import HeyGenClient

load_dotenv()

logger = structlog.get_logger(__name__)


class AvatarVideoWorker(BaseWorker):
    """Worker specialized for avatar video generation using HeyGen."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("avatar_video_worker", config)
    
    def _initialize_config(self):
        """Initialize HeyGen-specific configuration."""
        self.api_key = os.getenv("HEYGEN_API_KEY")
        self.base_url = os.getenv("HEYGEN_BASE_URL", "https://api.heygen.com/v1")
        
        if not self.api_key:
            logger.warning("HEYGEN_API_KEY not found - avatar video worker will be disabled")
            self.heygen_client = None
            return
        
        try:
            self.heygen_client = HeyGenClient(api_key=self.api_key, base_url=self.base_url)
            logger.info("HeyGen client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize HeyGen client", error=str(e))
            self.heygen_client = None
        
        self.config.update({
            "api_key": self.api_key,
            "base_url": self.base_url
        })
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process an avatar video generation task using HeyGen.
        
        Args:
            task: Avatar video generation task
            
        Returns:
            WorkerResult with video generation data
        """
        if not self.heygen_client:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="HeyGen client not initialized"
            )
        
        try:
            # Extract task parameters
            script = task.input_data.get("script", "")
            avatar_id = task.input_data.get("avatar_id")
            voice_id = task.input_data.get("voice_id")
            background = task.input_data.get("background", "office")
            video_format = task.input_data.get("video_format", "mp4")
            aspect_ratio = task.input_data.get("aspect_ratio", "16:9")
            
            if not script:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message="No script provided for avatar video generation"
                )
            
            # Create video with HeyGen
            video_result = await self.heygen_client.create_video(
                script=script,
                avatar_id=avatar_id,
                voice_id=voice_id,
                background=background,
                video_format=video_format,
                aspect_ratio=aspect_ratio
            )
            
            avatar_video_result = {
                "script": script,
                "avatar_id": avatar_id,
                "voice_id": voice_id,
                "background": background,
                "video_format": video_format,
                "aspect_ratio": aspect_ratio,
                "video_id": video_result.get("video_id"),
                "status": video_result.get("status", "processing"),
                "video_url": video_result.get("video_url"),
                "thumbnail_url": video_result.get("thumbnail_url"),
                "duration": video_result.get("duration"),
                "creation_time": datetime.utcnow().isoformat(),
                "heygen_response": video_result
            }
            
            logger.info(
                "Avatar video generation task completed successfully",
                task_id=task.task_id,
                video_id=video_result.get("video_id"),
                script_length=len(script)
            )
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="success",
                result=avatar_video_result,
                metadata={
                    "video_id": video_result.get("video_id"),
                    "avatar_id": avatar_id,
                    "script_length": len(script),
                    "aspect_ratio": aspect_ratio
                }
            )
            
        except Exception as e:
            logger.error("Avatar video generation task failed", task_id=task.task_id, error=str(e))
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Avatar video generation failed: {str(e)}"
            )
    
    async def health_check(self) -> bool:
        """Check if HeyGen API is accessible."""
        if not self.heygen_client:
            self.is_healthy = False
            return False
        
        try:
            self.is_healthy = await self.heygen_client.health_check()
            self.last_health_check = datetime.utcnow()
            return self.is_healthy
            
        except Exception as e:
            logger.warning("Avatar video worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False
    
    async def get_video_status(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a video generation.
        
        Args:
            video_id: HeyGen video ID
            
        Returns:
            Video status information or None if failed
        """
        if not self.heygen_client:
            return None
        
        try:
            status_result = await self.heygen_client.get_video_status(video_id)
            return status_result
        except Exception as e:
            logger.error("Failed to get video status", video_id=video_id, error=str(e))
            return None
    
    async def list_available_avatars(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of available avatars.
        
        Returns:
            List of available avatars or None if failed
        """
        if not self.heygen_client:
            return None
        
        try:
            avatars_result = await self.heygen_client.list_avatars()
            return avatars_result.get("avatars", [])
        except Exception as e:
            logger.error("Failed to get available avatars", error=str(e))
            return None
    
    async def list_available_voices(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of available voices.
        
        Returns:
            List of available voices or None if failed
        """
        if not self.heygen_client:
            return None
        
        try:
            voices_result = await self.heygen_client.list_voices()
            return voices_result.get("voices", [])
        except Exception as e:
            logger.error("Failed to get available voices", error=str(e))
            return None
    
    async def create_social_media_video(
        self, 
        script: str, 
        platform: str = "general",
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an avatar video optimized for social media platforms.
        
        Args:
            script: Video script
            platform: Target social media platform
            avatar_id: Specific avatar to use
            voice_id: Specific voice to use
            
        Returns:
            Generated video data or None if failed
        """
        # Platform-specific optimization
        platform_configs = {
            "instagram": {"aspect_ratio": "9:16", "background": "modern"},
            "instagram_story": {"aspect_ratio": "9:16", "background": "minimal"},
            "tiktok": {"aspect_ratio": "9:16", "background": "trendy"},
            "youtube": {"aspect_ratio": "16:9", "background": "professional"},
            "youtube_shorts": {"aspect_ratio": "9:16", "background": "dynamic"},
            "twitter": {"aspect_ratio": "16:9", "background": "clean"},
            "linkedin": {"aspect_ratio": "16:9", "background": "professional"},
            "facebook": {"aspect_ratio": "16:9", "background": "friendly"},
            "general": {"aspect_ratio": "16:9", "background": "office"}
        }
        
        config = platform_configs.get(platform.lower(), platform_configs["general"])
        
        task = WorkerTask(
            task_id=f"social_avatar_video_{platform}_{datetime.utcnow().timestamp()}",
            task_type="social_avatar_video",
            input_data={
                "script": script,
                "avatar_id": avatar_id,
                "voice_id": voice_id,
                "background": config["background"],
                "aspect_ratio": config["aspect_ratio"],
                "video_format": "mp4"
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def create_branded_video(
        self, 
        script: str, 
        brand_guidelines: Optional[Dict[str, Any]] = None,
        avatar_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a branded avatar video.
        
        Args:
            script: Video script
            brand_guidelines: Brand guidelines for video styling
            avatar_id: Specific avatar to use
            
        Returns:
            Generated branded video data or None if failed
        """
        # Apply brand guidelines
        background = "professional"
        if brand_guidelines:
            background = brand_guidelines.get("video_background", "professional")
            
            # Modify script to include brand messaging if needed
            brand_tone = brand_guidelines.get("tone", "professional")
            if brand_tone == "casual":
                background = "casual"
            elif brand_tone == "modern":
                background = "modern"
        
        task = WorkerTask(
            task_id=f"branded_avatar_video_{datetime.utcnow().timestamp()}",
            task_type="branded_avatar_video",
            input_data={
                "script": script,
                "avatar_id": avatar_id,
                "background": background,
                "aspect_ratio": "16:9",
                "video_format": "mp4"
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def create_video_series(
        self, 
        scripts: List[str], 
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        background: str = "office"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Create a series of related avatar videos.
        
        Args:
            scripts: List of video scripts
            avatar_id: Avatar to use for all videos
            voice_id: Voice to use for all videos
            background: Background setting for all videos
            
        Returns:
            List of generated video data or None if failed
        """
        tasks = []
        for i, script in enumerate(scripts):
            task = WorkerTask(
                task_id=f"video_series_{i}_{datetime.utcnow().timestamp()}",
                task_type="avatar_video_series",
                input_data={
                    "script": script,
                    "avatar_id": avatar_id,
                    "voice_id": voice_id,
                    "background": background,
                    "aspect_ratio": "16:9",
                    "video_format": "mp4"
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