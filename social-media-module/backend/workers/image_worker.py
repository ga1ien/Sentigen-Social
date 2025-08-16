"""
Image Worker using OpenAI's gpt-image-1 model for advanced image generation and visual content creation.
"""

import os
import base64
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from dotenv import load_dotenv
import httpx

from workers.base_worker import BaseWorker, WorkerTask, WorkerResult

load_dotenv()

logger = structlog.get_logger(__name__)


class ImageWorker(BaseWorker):
    """Worker specialized for image generation using OpenAI's gpt-image-1 model."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("image_worker", config)
    
    def _initialize_config(self):
        """Initialize gpt-image-1 specific configuration for image generation."""
        self.api_key = os.getenv("OPENAI_IMAGE_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
        self.base_url = os.getenv("OPENAI_IMAGE_BASE_URL", "https://api.openai.com/v1")
        
        if not self.api_key:
            logger.warning("OPENAI_IMAGE_API_KEY not found - image worker will be disabled")
            return
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.config.update({
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url
        })
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process an image generation task using GPT-4o.
        
        Args:
            task: Image generation task
            
        Returns:
            WorkerResult with generated image data
        """
        if not self.api_key:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="OpenAI API key not configured for image generation"
            )
        
        try:
            # Extract task parameters
            prompt = task.input_data.get("prompt", "")
            style = task.input_data.get("style", "natural")
            size = task.input_data.get("size", "1024x1024")
            quality = task.input_data.get("quality", "high")  # gpt-image-1 default to high
            n_images = task.input_data.get("n_images", 1)
            response_format = task.input_data.get("response_format", "url")
            
            # Validate gpt-image-1 parameters
            valid_qualities = ["low", "medium", "high", "auto"]
            if quality not in valid_qualities:
                quality = "high"
            
            valid_sizes = ["1024x1024", "1024x1536", "1536x1024"]
            if size not in valid_sizes:
                size = "1024x1024"
            
            if not prompt:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message="No prompt provided for image generation"
                )
            
            # Enhance prompt based on style
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            # Prepare API request for gpt-image-1
            # Note: gpt-image-1 only returns base64-encoded images, not URLs
            payload = {
                "model": self.model,
                "prompt": enhanced_prompt,
                "size": size,
                "quality": quality,  # gpt-image-1 supports: low, medium, high, auto
                "response_format": "b64_json"  # gpt-image-1 only supports b64_json
            }
            
            # gpt-image-1 generates one image per request
            # For multiple images, we'll need to make multiple requests
            
            # Make API call(s) - gpt-image-1 generates one image per request
            images = []
            async with httpx.AsyncClient(timeout=120.0) as client:
                for i in range(n_images):
                    try:
                        response = await client.post(
                            f"{self.base_url}/images/generations",
                            json=payload,
                            headers=self.headers
                        )
                        
                        response.raise_for_status()
                        result_data = response.json()
                        
                        # Process the generated image
                        for img_data in result_data.get("data", []):
                            b64_data = img_data.get("b64_json")
                            
                            # For gpt-image-1, convert b64 to URL if requested
                            image_url = None
                            if response_format == "url" and b64_data:
                                # Save base64 image and create URL
                                image_url = await self._save_b64_image_to_url(b64_data, i + 1)
                            
                            image_info = {
                                "url": image_url if response_format == "url" else None,
                                "b64_json": b64_data if response_format == "b64_json" else None,
                                "revised_prompt": img_data.get("revised_prompt"),
                                "size": size,
                                "quality": quality,
                                "model": self.model,
                                "generation_index": i + 1
                            }
                            images.append(image_info)
                    except Exception as e:
                        logger.error("Failed to generate image", attempt=i+1, error=str(e))
                        # Continue with other images if one fails
                        continue
                
                image_result = {
                    "prompt": prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "style": style,
                    "images": images,
                    "model_used": self.model,
                    "generation_params": {
                        "size": size,
                        "quality": quality,
                        "n_images": len(images)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(
                    "Image generation task completed successfully",
                    task_id=task.task_id,
                    prompt_length=len(prompt),
                    images_generated=len(images),
                    model=self.model
                )
                
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="success",
                    result=image_result,
                    metadata={
                        "model": self.model,
                        "images_count": len(images),
                        "style": style,
                        "size": size
                    }
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = f"OpenAI API error: {e.response.status_code}"
            try:
                error_response = e.response.json()
                error_detail += f" - {error_response.get('error', {}).get('message', str(e))}"
            except:
                error_detail += f" - {str(e)}"
            
            logger.error("Image generation task failed", task_id=task.task_id, error=error_detail)
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=error_detail
            )
            
        except Exception as e:
            logger.error("Unexpected error in image generation task", task_id=task.task_id, error=str(e))
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Image generation failed: {str(e)}"
            )
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance the prompt based on the requested style."""
        style_enhancements = {
            "natural": "photorealistic, natural lighting, high quality",
            "artistic": "artistic, creative, stylized, beautiful composition",
            "professional": "professional, clean, corporate, high-end",
            "social_media": "eye-catching, vibrant, social media optimized, engaging",
            "minimalist": "minimalist, clean, simple, elegant design",
            "vintage": "vintage style, retro, classic aesthetic",
            "modern": "modern, contemporary, sleek design",
            "cartoon": "cartoon style, illustrated, colorful, fun",
            "abstract": "abstract art, creative, unique perspective",
            "brand": "brand-focused, professional, marketing-ready"
        }
        
        enhancement = style_enhancements.get(style, style_enhancements["natural"])
        
        # Combine original prompt with style enhancement
        if enhancement not in prompt.lower():
            enhanced_prompt = f"{prompt}, {enhancement}"
        else:
            enhanced_prompt = prompt
        
        return enhanced_prompt
    
    async def health_check(self) -> bool:
        """Check if OpenAI image generation API is accessible."""
        if not self.api_key:
            self.is_healthy = False
            return False
        
        try:
            # Simple test generation
            payload = {
                "model": self.model,
                "prompt": "A simple test image",
                "n": 1,
                "size": "256x256"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    json=payload,
                    headers=self.headers
                )
                
                self.is_healthy = response.status_code == 200
                self.last_health_check = datetime.utcnow()
                
                return self.is_healthy
                
        except Exception as e:
            logger.warning("Image worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False
    
    async def generate_social_media_image(
        self, 
        prompt: str, 
        platform: str = "general",
        style: str = "social_media"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an image optimized for social media platforms.
        
        Args:
            prompt: Image generation prompt
            platform: Target social media platform
            style: Image style
            
        Returns:
            Generated image data or None if failed
        """
        # Platform-specific size optimization
        platform_sizes = {
            "instagram": "1024x1024",  # Square posts
            "instagram_story": "1024x1792",  # 9:16 ratio
            "twitter": "1200x675",  # 16:9 ratio
            "facebook": "1200x630",  # 1.91:1 ratio
            "linkedin": "1200x627",  # Similar to Facebook
            "pinterest": "1000x1500",  # 2:3 ratio
            "youtube": "1280x720",  # 16:9 ratio
            "general": "1024x1024"
        }
        
        size = platform_sizes.get(platform.lower(), "1024x1024")
        
        # Enhance prompt for social media
        social_prompt = f"{prompt}, optimized for {platform}, engaging, high-quality"
        
        task = WorkerTask(
            task_id=f"social_image_{platform}_{datetime.utcnow().timestamp()}",
            task_type="social_media_image",
            input_data={
                "prompt": social_prompt,
                "style": style,
                "size": size,
                "quality": "high",  # gpt-image-1 uses high quality by default
                "response_format": "url"
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def generate_brand_image(
        self, 
        prompt: str, 
        brand_guidelines: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a brand-consistent image.
        
        Args:
            prompt: Image generation prompt
            brand_guidelines: Brand guidelines including colors, style, etc.
            
        Returns:
            Generated brand image data or None if failed
        """
        # Incorporate brand guidelines into prompt
        brand_prompt = prompt
        
        if brand_guidelines:
            colors = brand_guidelines.get("colors", [])
            style_guide = brand_guidelines.get("style", "professional")
            tone = brand_guidelines.get("tone", "modern")
            
            if colors:
                brand_prompt += f", using brand colors: {', '.join(colors)}"
            
            brand_prompt += f", {style_guide} style, {tone} aesthetic"
        
        task = WorkerTask(
            task_id=f"brand_image_{datetime.utcnow().timestamp()}",
            task_type="brand_image",
            input_data={
                "prompt": brand_prompt,
                "style": "brand",
                "size": "1024x1024",
                "quality": "high",  # gpt-image-1 uses high quality by default
                "response_format": "url"
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def generate_image_variations(
        self, 
        base_prompt: str, 
        variations: int = 3,
        style: str = "natural"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Generate multiple variations of an image concept.
        
        Args:
            base_prompt: Base prompt for variations
            variations: Number of variations to generate
            style: Image style
            
        Returns:
            List of generated image variations or None if failed
        """
        variation_prompts = [
            f"{base_prompt}, variation {i+1}, unique perspective"
            for i in range(variations)
        ]
        
        tasks = []
        for i, prompt in enumerate(variation_prompts):
            task = WorkerTask(
                task_id=f"image_variation_{i}_{datetime.utcnow().timestamp()}",
                task_type="image_variation",
                input_data={
                    "prompt": prompt,
                    "style": style,
                    "size": "1024x1024",
                    "quality": "standard",
                    "response_format": "url"
                }
            )
            tasks.append(task)
        
        # Process variations concurrently
        results = await self.batch_process(tasks)
        
        successful_results = [
            result.result for result in results 
            if result.status == "success"
        ]
        
        return successful_results if successful_results else None
    
    async def _save_b64_image_to_url(self, b64_data: str, index: int = 1) -> Optional[str]:
        """
        Save base64 image data to file and return URL.
        
        Args:
            b64_data: Base64 encoded image data
            index: Image index for unique naming
            
        Returns:
            URL to the saved image or None if failed
        """
        try:
            # Create images directory if it doesn't exist
            images_dir = Path("generated_images")
            images_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            image_id = str(uuid.uuid4())
            filename = f"gpt_image_1_{image_id}_{index}.png"
            file_path = images_dir / filename
            
            # Decode and save base64 image
            image_bytes = base64.b64decode(b64_data)
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            # Return URL (adjust base URL as needed for your deployment)
            base_url = os.getenv("IMAGE_BASE_URL", "http://localhost:8000")
            image_url = f"{base_url}/generated_images/{filename}"
            
            logger.info("Saved gpt-image-1 image", filename=filename, url=image_url)
            return image_url
            
        except Exception as e:
            logger.error("Failed to save base64 image", error=str(e))
            return None