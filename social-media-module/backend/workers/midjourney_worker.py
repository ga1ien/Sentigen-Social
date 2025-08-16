"""
Midjourney Worker for image and video generation via CometAPI.
Handles both artistic image creation and image-to-video conversion.
"""

import os
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
import structlog

from .base_worker import BaseWorker, WorkerTask, WorkerResult

logger = structlog.get_logger(__name__)


class MidjourneyWorker(BaseWorker):
    """Worker specialized for Midjourney image and video generation via CometAPI."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("midjourney_worker", config)
    
    def _initialize_config(self):
        """Initialize CometAPI configuration for Midjourney."""
        self.api_key = os.getenv("COMETAPI_KEY")
        self.base_url = os.getenv("COMETAPI_BASE_URL", "https://api.cometapi.com")
        self.mode = os.getenv("MIDJOURNEY_MODE", "fast")
        self.version = os.getenv("MIDJOURNEY_VERSION", "6.1")
        
        if not self.api_key:
            logger.warning("COMETAPI_KEY not found - Midjourney worker will be disabled")
            return
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.config.update({
            "api_key": self.api_key,
            "base_url": self.base_url,
            "mode": self.mode,
            "version": self.version
        })
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process a Midjourney generation task (image or video).
        
        Args:
            task: Midjourney generation task
            
        Returns:
            WorkerResult with generation data
        """
        if not self.api_key:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="CometAPI key not configured for Midjourney access"
            )
        
        try:
            # Extract task parameters
            task_type = task.input_data.get("type", "image")  # "image" or "video"
            prompt = task.input_data.get("prompt", "")
            
            if task_type == "image":
                result = await self._generate_image(task)
            elif task_type == "video":
                result = await self._generate_video(task)
            else:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message=f"Unsupported task type: {task_type}"
                )
            
            return result
            
        except Exception as e:
            logger.error("Midjourney worker task failed", 
                        task_id=task.task_id, 
                        error=str(e))
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Midjourney generation failed: {str(e)}"
            )
    
    async def _generate_image(self, task: WorkerTask) -> WorkerResult:
        """Generate an image using Midjourney via CometAPI."""
        prompt = task.input_data.get("prompt", "")
        aspect_ratio = task.input_data.get("aspect_ratio", "1:1")
        style = task.input_data.get("style", "")
        quality = task.input_data.get("quality", "standard")
        
        # Enhance prompt with Midjourney-specific parameters
        enhanced_prompt = self._enhance_image_prompt(prompt, aspect_ratio, style, quality)
        
        # Submit image generation task
        payload = {
            "prompt": enhanced_prompt,
            "mode": self.mode
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Submit the task
            response = await client.post(
                f"{self.base_url}/mj/submit/imagine",
                json=payload,
                headers=self.headers
            )
            
            response.raise_for_status()
            submit_result = response.json()
            
            if submit_result.get("code") != 1:
                raise Exception(f"Midjourney submission failed: {submit_result.get('description')}")
            
            task_id = submit_result.get("result")
            
            # Poll for completion
            image_result = await self._poll_for_completion(task_id, "image")
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="completed",
                result={
                    "type": "image",
                    "midjourney_task_id": task_id,
                    "prompt": enhanced_prompt,
                    "images": image_result.get("images", []),
                    "metadata": {
                        "aspect_ratio": aspect_ratio,
                        "style": style,
                        "quality": quality,
                        "mode": self.mode
                    }
                },
                error_message=None
            )
    
    async def _generate_video(self, task: WorkerTask) -> WorkerResult:
        """Generate a video using Midjourney via CometAPI."""
        prompt = task.input_data.get("prompt", "")
        source_image = task.input_data.get("source_image", "")  # URL or base64
        video_type = task.input_data.get("video_type", "vid_1.1_i2v_480")
        motion = task.input_data.get("motion", "low")
        animate_mode = task.input_data.get("animate_mode", "manual")
        
        # Prepare video generation prompt
        if source_image:
            video_prompt = f"{source_image} {prompt}"
        else:
            video_prompt = prompt
        
        # Submit video generation task
        payload = {
            "prompt": video_prompt,
            "videoType": video_type,
            "mode": self.mode,
            "animateMode": animate_mode,
            "motion": motion
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Submit the task
            response = await client.post(
                f"{self.base_url}/mj/submit/video",
                json=payload,
                headers=self.headers
            )
            
            response.raise_for_status()
            submit_result = response.json()
            
            if submit_result.get("code") != 1:
                raise Exception(f"Midjourney video submission failed: {submit_result.get('description')}")
            
            task_id = submit_result.get("result")
            
            # Poll for completion (videos take longer)
            video_result = await self._poll_for_completion(task_id, "video", timeout=600)
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="completed",
                result={
                    "type": "video",
                    "midjourney_task_id": task_id,
                    "prompt": video_prompt,
                    "video_url": video_result.get("video_url"),
                    "thumbnail_url": video_result.get("thumbnail_url"),
                    "metadata": {
                        "video_type": video_type,
                        "motion": motion,
                        "animate_mode": animate_mode,
                        "mode": self.mode,
                        "source_image": source_image
                    }
                },
                error_message=None
            )
    
    async def _poll_for_completion(self, task_id: str, content_type: str, timeout: int = 300) -> Dict[str, Any]:
        """Poll CometAPI for task completion."""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/mj/task/{task_id}/fetch",
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") == 1:
                    task_data = result.get("result", {})
                    status = task_data.get("status")
                    
                    if status == "SUCCESS":
                        if content_type == "image":
                            return {
                                "images": task_data.get("imageUrl", []),
                                "status": status
                            }
                        else:  # video
                            return {
                                "video_url": task_data.get("videoUrl"),
                                "thumbnail_url": task_data.get("thumbnailUrl"),
                                "status": status
                            }
                    elif status == "FAILURE":
                        raise Exception(f"Midjourney task failed: {task_data.get('failReason', 'Unknown error')}")
                
                # Wait before next poll
                await asyncio.sleep(10)
        
        raise Exception(f"Midjourney task {task_id} timed out after {timeout} seconds")
    
    def _enhance_image_prompt(self, prompt: str, aspect_ratio: str, style: str, quality: str) -> str:
        """Enhance the prompt with Midjourney-specific parameters."""
        enhanced_prompt = prompt
        
        # Add aspect ratio
        if aspect_ratio and aspect_ratio != "1:1":
            enhanced_prompt += f" --aspect {aspect_ratio}"
        
        # Add style parameters
        if style:
            style_mappings = {
                "photorealistic": "--style raw --v 6.1",
                "artistic": "--style expressive --v 6.1",
                "anime": "--niji 6",
                "cinematic": "--style cinematic --v 6.1",
                "minimalist": "--style minimalist --v 6.1"
            }
            if style.lower() in style_mappings:
                enhanced_prompt += f" {style_mappings[style.lower()]}"
        
        # Add quality parameters
        if quality == "high":
            enhanced_prompt += " --quality 2"
        elif quality == "ultra":
            enhanced_prompt += " --quality 2 --stylize 1000"
        
        # Add version if not already specified
        if "--v " not in enhanced_prompt and "--niji" not in enhanced_prompt:
            enhanced_prompt += f" --v {self.version}"
        
        return enhanced_prompt
    
    async def health_check(self) -> bool:
        """Check if CometAPI is accessible for Midjourney."""
        if not self.api_key:
            self.is_healthy = False
            return False
        
        try:
            # Simple test request to check API availability
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/mj/task/test/fetch",  # Test endpoint
                    headers=self.headers
                )
                
                # CometAPI returns 200 even for non-existent tasks, so we check for valid JSON
                self.is_healthy = response.status_code == 200
                self.last_health_check = datetime.utcnow()
                
                return self.is_healthy
                
        except Exception as e:
            logger.warning("Midjourney worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False
    
    async def get_task_status(self, midjourney_task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a Midjourney task.
        
        Args:
            midjourney_task_id: The Midjourney task ID
            
        Returns:
            Task status information
        """
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/mj/task/{midjourney_task_id}/fetch",
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") == 1:
                    return result.get("result", {})
                
                return None
                
        except Exception as e:
            logger.error("Failed to get Midjourney task status", 
                        task_id=midjourney_task_id, 
                        error=str(e))
            return None
    
    async def upscale_image(self, task_id: str, index: int) -> Optional[Dict[str, Any]]:
        """
        Upscale a specific image from a Midjourney generation.
        
        Args:
            task_id: Original Midjourney task ID
            index: Image index to upscale (1-4)
            
        Returns:
            Upscaled image result
        """
        if not self.api_key:
            return None
        
        try:
            payload = {
                "taskId": task_id,
                "action": f"UPSCALE",
                "index": index
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/mj/submit/action",
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") == 1:
                    new_task_id = result.get("result")
                    # Poll for completion
                    upscale_result = await self._poll_for_completion(new_task_id, "image")
                    return upscale_result
                
                return None
                
        except Exception as e:
            logger.error("Failed to upscale Midjourney image", 
                        task_id=task_id, 
                        index=index, 
                        error=str(e))
            return None
