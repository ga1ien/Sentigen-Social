#!/usr/bin/env python3
"""
HeyGen API Client for Avatar Video Generation
Integrates with HeyGen's v2 API for creating avatar videos
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import structlog

# Configure logging
logger = structlog.get_logger(__name__)


class VideoStatus(Enum):
    """Video generation status"""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    PENDING = "pending"


class AvatarType(Enum):
    """Avatar types supported by HeyGen"""

    AVATAR = "avatar"
    TALKING_PHOTO = "talking_photo"


class AspectRatio(Enum):
    """Supported aspect ratios"""

    PORTRAIT = "portrait"  # 9:16 (720x1280)
    LANDSCAPE = "landscape"  # 16:9 (1280x720)
    SQUARE = "square"  # 1:1 (720x720)


@dataclass
class AvatarProfile:
    """Avatar profile data structure"""

    id: str
    name: str
    avatar_id: str
    voice_id: str
    avatar_type: AvatarType
    description: Optional[str] = None
    preview_url: Optional[str] = None
    gender: Optional[str] = None
    age_range: Optional[str] = None
    style: Optional[str] = None


@dataclass
class VideoGenerationRequest:
    """Video generation request data"""

    script: str
    avatar_profile: AvatarProfile
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    voice_speed: float = 1.0
    enable_captions: bool = True
    background_color: str = "#ffffff"
    background_type: str = "color"
    background_url: Optional[str] = None
    title: Optional[str] = None


@dataclass
class VideoGenerationResponse:
    """Video generation response data"""

    video_id: str
    status: VideoStatus
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class HeyGenAPIError(Exception):
    """Custom exception for HeyGen API errors"""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class HeyGenClient:
    """HeyGen API client for avatar video generation"""

    # HeyGen API endpoints
    BASE_URL = "https://api.heygen.com"
    VIDEO_GENERATE_URL = f"{BASE_URL}/v2/video/generate"
    VIDEO_STATUS_URL = f"{BASE_URL}/v1/video_status.get"
    AVATARS_URL = f"{BASE_URL}/v2/avatars"
    VOICES_URL = f"{BASE_URL}/v2/voices"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize HeyGen client"""
        self.api_key = api_key or os.getenv("HEYGEN_API_KEY")
        if not self.api_key:
            raise ValueError("HeyGen API key is required. Set HEYGEN_API_KEY environment variable.")

        self.session = None
        logger.info("HeyGen client initialized", api_key_length=len(self.api_key))

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300), headers=self._get_headers()  # 5 minute timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers for HeyGen requests"""
        return {
            "X-Api-Key": self.api_key,  # Note: HeyGen uses X-Api-Key, not Bearer
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Sentigen-Social/1.0",
        }

    def _clean_script(self, script: str) -> str:
        """Clean script text for video generation"""
        # Remove emojis and special characters that might cause issues
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE,
        )

        cleaned = emoji_pattern.sub(r"", script)

        # Clean up extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Ensure minimum length
        if len(cleaned) < 3:
            raise ValueError("Script too short after cleaning")

        # Ensure maximum length (HeyGen has limits)
        if len(cleaned) > 5000:
            cleaned = cleaned[:5000]
            logger.warning("Script truncated to 5000 characters", original_length=len(script))

        return cleaned

    def _get_dimensions(self, aspect_ratio: AspectRatio) -> Tuple[int, int]:
        """Get video dimensions for aspect ratio"""
        dimensions = {
            AspectRatio.PORTRAIT: (720, 1280),  # 9:16
            AspectRatio.LANDSCAPE: (1280, 720),  # 16:9
            AspectRatio.SQUARE: (720, 720),  # 1:1
        }
        return dimensions[aspect_ratio]

    def _build_character_settings(self, avatar_profile: AvatarProfile) -> Dict[str, Any]:
        """Build character settings for HeyGen API"""
        if avatar_profile.avatar_type == AvatarType.AVATAR:
            # Regular avatar settings
            return {
                "type": "avatar",
                "avatar_id": avatar_profile.avatar_id,
                "scale": 1.0,
                "offset": {"x": 0, "y": 0},
                "avatar_style": "normal",
            }
        else:
            # UGC/Talking photo settings
            return {
                "type": "talking_photo",
                "talking_photo_id": avatar_profile.avatar_id,  # Different field name!
                "scale": 1.0,
                "offset": {"x": 0, "y": 0},
                "talking_style": "expressive",
                "expression": "happy",
                "super_resolution": True,
                "matting": False,
            }

    def _build_voice_settings(
        self, script: str, avatar_profile: AvatarProfile, voice_speed: float = 1.0
    ) -> Dict[str, Any]:
        """Build voice settings for HeyGen API"""
        return {
            "type": "text",
            "input_text": script,
            "voice_id": avatar_profile.voice_id,
            "speed": max(0.5, min(2.0, voice_speed)),  # Clamp speed between 0.5 and 2.0
        }

    def _build_background_settings(
        self, background_type: str = "color", background_color: str = "#ffffff", background_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build background settings for HeyGen API"""
        if background_type == "color":
            return {"type": "color", "value": background_color}
        elif background_type == "image" and background_url:
            return {"type": "image", "url": background_url}
        elif background_type == "video" and background_url:
            return {"type": "video", "url": background_url}
        else:
            # Default to white background
            return {"type": "color", "value": "#ffffff"}

    def _build_payload(self, request: VideoGenerationRequest) -> Dict[str, Any]:
        """Build complete HeyGen API payload"""
        # Clean script
        cleaned_script = self._clean_script(request.script)

        # Get dimensions
        width, height = self._get_dimensions(request.aspect_ratio)

        # Build payload components
        character_settings = self._build_character_settings(request.avatar_profile)
        voice_settings = self._build_voice_settings(cleaned_script, request.avatar_profile, request.voice_speed)
        background_settings = self._build_background_settings(
            request.background_type, request.background_color, request.background_url
        )

        # Complete payload
        payload = {
            "video_inputs": [
                {"character": character_settings, "voice": voice_settings, "background": background_settings}
            ],
            "dimension": {"width": width, "height": height},
            "caption": request.enable_captions,
            "title": request.title or "Sentigen Social Video",
        }

        logger.info(
            "Built HeyGen payload",
            avatar_type=request.avatar_profile.avatar_type.value,
            aspect_ratio=request.aspect_ratio.value,
            script_length=len(cleaned_script),
        )

        return payload

    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResponse:
        """Generate a video using HeyGen API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            # Build payload
            payload = self._build_payload(request)

            logger.info(
                "Sending video generation request to HeyGen",
                avatar_name=request.avatar_profile.name,
                script_preview=request.script[:100] + "..." if len(request.script) > 100 else request.script,
            )

            # Send request
            async with self.session.post(self.VIDEO_GENERATE_URL, json=payload) as response:
                response_data = await response.json()

                if response.status != 200:
                    error_msg = response_data.get("message", f"HTTP {response.status}")
                    logger.error(
                        "HeyGen video generation failed",
                        status_code=response.status,
                        error=error_msg,
                        response_data=response_data,
                    )
                    raise HeyGenAPIError(error_msg, response.status, response_data)

                # Extract video ID
                video_id = response_data.get("data", {}).get("video_id")
                if not video_id:
                    raise HeyGenAPIError("No video ID in response", response.status, response_data)

                logger.info("Video generation started", video_id=video_id)

                return VideoGenerationResponse(
                    video_id=video_id, status=VideoStatus.PROCESSING, created_at=datetime.now()
                )

        except aiohttp.ClientError as e:
            logger.error("Network error during video generation", error=str(e))
            raise HeyGenAPIError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error during video generation", error=str(e))
            raise HeyGenAPIError(f"Unexpected error: {str(e)}")

    async def get_video_status(self, video_id: str) -> VideoGenerationResponse:
        """Get video generation status"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            # Build status URL
            status_url = f"{self.VIDEO_STATUS_URL}?video_id={video_id}"

            logger.debug("Checking video status", video_id=video_id)

            # Send request
            async with self.session.get(status_url) as response:
                response_data = await response.json()

                if response.status != 200:
                    error_msg = response_data.get("message", f"HTTP {response.status}")
                    logger.error(
                        "HeyGen status check failed", video_id=video_id, status_code=response.status, error=error_msg
                    )
                    raise HeyGenAPIError(error_msg, response.status, response_data)

                # Extract status data
                data = response_data.get("data", {})
                status_str = data.get("status", "unknown").lower()

                # Map HeyGen status to our enum
                if status_str == "completed":
                    status = VideoStatus.COMPLETED
                elif status_str in ["failed", "error"]:
                    status = VideoStatus.FAILED
                elif status_str == "processing":
                    status = VideoStatus.PROCESSING
                else:
                    status = VideoStatus.PENDING

                # Extract video details
                video_url = data.get("video_url")
                thumbnail_url = data.get("thumbnail_url")
                duration = data.get("duration")
                error_message = data.get("error") if status == VideoStatus.FAILED else None

                logger.info(
                    "Video status retrieved", video_id=video_id, status=status.value, has_video_url=bool(video_url)
                )

                return VideoGenerationResponse(
                    video_id=video_id,
                    status=status,
                    video_url=video_url,
                    thumbnail_url=thumbnail_url,
                    duration_seconds=duration,
                    error_message=error_message,
                )

        except aiohttp.ClientError as e:
            logger.error("Network error during status check", video_id=video_id, error=str(e))
            raise HeyGenAPIError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error during status check", video_id=video_id, error=str(e))
            raise HeyGenAPIError(f"Unexpected error: {str(e)}")

    async def list_avatars(self) -> List[Dict[str, Any]]:
        """List available avatars from HeyGen"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(self.AVATARS_URL) as response:
                response_data = await response.json()

                if response.status != 200:
                    error_msg = response_data.get("message", f"HTTP {response.status}")
                    raise HeyGenAPIError(error_msg, response.status, response_data)

                avatars = response_data.get("data", {}).get("avatars", [])
                logger.info("Retrieved avatars from HeyGen", count=len(avatars))

                return avatars

        except aiohttp.ClientError as e:
            logger.error("Network error listing avatars", error=str(e))
            raise HeyGenAPIError(f"Network error: {str(e)}")

    async def list_voices(self) -> List[Dict[str, Any]]:
        """List available voices from HeyGen"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(self.VOICES_URL) as response:
                response_data = await response.json()

                if response.status != 200:
                    error_msg = response_data.get("message", f"HTTP {response.status}")
                    raise HeyGenAPIError(error_msg, response.status, response_data)

                voices = response_data.get("data", {}).get("voices", [])
                logger.info("Retrieved voices from HeyGen", count=len(voices))

                return voices

        except aiohttp.ClientError as e:
            logger.error("Network error listing voices", error=str(e))
            raise HeyGenAPIError(f"Network error: {str(e)}")


# Utility functions for easy usage
async def create_video_from_research(
    research_content: str,
    avatar_name: str = "Sarah",
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT,
    voice_speed: float = 1.0,
) -> VideoGenerationResponse:
    """
    Convenience function to create video from research content

    Args:
        research_content: The script/content to convert to video
        avatar_name: Name of avatar to use (default: Sarah)
        aspect_ratio: Video aspect ratio (default: portrait)
        voice_speed: Voice speed multiplier (default: 1.0)

    Returns:
        VideoGenerationResponse with video_id and status
    """
    # This would typically load avatar profile from database
    # For now, using a default profile
    default_profile = AvatarProfile(
        id="default",
        name=avatar_name,
        avatar_id="a58345668aa2444c8229923ef67a3e76",  # Sarah's avatar ID
        voice_id="b54cd1be94d848879a0acd2f7138fd3c",  # Sarah's voice ID
        avatar_type=AvatarType.TALKING_PHOTO,
    )

    request = VideoGenerationRequest(
        script=research_content,
        avatar_profile=default_profile,
        aspect_ratio=aspect_ratio,
        voice_speed=voice_speed,
        title=f"Research Video - {datetime.now().strftime('%Y-%m-%d')}",
    )

    async with HeyGenClient() as client:
        return await client.generate_video(request)


async def check_video_status(video_id: str) -> VideoGenerationResponse:
    """
    Convenience function to check video status

    Args:
        video_id: HeyGen video ID

    Returns:
        VideoGenerationResponse with current status
    """
    async with HeyGenClient() as client:
        return await client.get_video_status(video_id)


# Example usage
if __name__ == "__main__":

    async def test_heygen_integration():
        """Test HeyGen integration"""
        try:
            # Test video creation
            research_script = """
            Today we're exploring the latest trends in AI automation tools.
            Based on our research, ChatGPT and similar AI tools are seeing massive growth,
            with over 5000% increase in search interest.
            This presents a huge opportunity for content creators and businesses
            to leverage these tools for productivity and growth.
            """

            print("🎬 Creating video from research content...")
            response = await create_video_from_research(
                research_content=research_script, avatar_name="Sarah", aspect_ratio=AspectRatio.PORTRAIT
            )

            print(f"✅ Video creation started: {response.video_id}")

            # Poll for completion
            print("⏳ Polling for video completion...")
            max_attempts = 60  # 5 minutes max
            attempt = 0

            while attempt < max_attempts:
                status_response = await check_video_status(response.video_id)
                print(f"📊 Status: {status_response.status.value}")

                if status_response.status == VideoStatus.COMPLETED:
                    print(f"🎉 Video completed: {status_response.video_url}")
                    break
                elif status_response.status == VideoStatus.FAILED:
                    print(f"❌ Video failed: {status_response.error_message}")
                    break

                await asyncio.sleep(5)  # Wait 5 seconds
                attempt += 1

            if attempt >= max_attempts:
                print("⏰ Timeout waiting for video completion")

        except Exception as e:
            print(f"❌ Test failed: {e}")

    # Run test
    asyncio.run(test_heygen_integration())
