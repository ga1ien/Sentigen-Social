"""
HeyGen API client for video generation.
"""

import os
import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger(__name__)


class HeyGenClient:
    """
    Async client for interacting with the HeyGen API.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the HeyGen client.
        
        Args:
            api_key: HeyGen API key. If None, will use HEYGEN_API_KEY env var.
            base_url: HeyGen API base URL. If None, will use HEYGEN_BASE_URL env var.
        """
        self.api_key = api_key or os.getenv("HEYGEN_API_KEY")
        self.base_url = base_url or os.getenv("HEYGEN_BASE_URL", "https://api.heygen.com/v1")
        
        if not self.api_key:
            raise ValueError("HeyGen API key is required. Set HEYGEN_API_KEY environment variable.")
        
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_video(
        self,
        script: str,
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        background: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a video using HeyGen API.
        
        Args:
            script: The text script for the video
            avatar_id: ID of the avatar to use
            voice_id: ID of the voice to use
            background: Background setting
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the API response
        """
        payload = {
            "script": script,
            "avatar_id": avatar_id,
            "voice_id": voice_id,
            "background": background,
            **kwargs
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        logger.info("Creating HeyGen video", script_length=len(script))
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/video/generate",
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info("HeyGen video creation successful", 
                           video_id=result.get("video_id"))
                
                return result
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                error_detail = error_response.get("message", str(e))
            except:
                error_detail = str(e)
            
            logger.error("HeyGen API error", 
                        status_code=e.response.status_code,
                        error=error_detail)
            
            raise Exception(f"HeyGen API error ({e.response.status_code}): {error_detail}")
            
        except Exception as e:
            logger.error("Unexpected error creating HeyGen video", error=str(e))
            raise Exception(f"Failed to create HeyGen video: {str(e)}")
    
    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Get the status of a video generation.
        
        Args:
            video_id: The video ID to check
            
        Returns:
            Dict containing video status information
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/video/{video_id}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("Failed to get HeyGen video status", 
                        video_id=video_id,
                        status_code=e.response.status_code)
            raise Exception(f"Failed to get video status: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error getting video status", error=str(e))
            raise Exception(f"Failed to get video status: {str(e)}")
    
    async def list_avatars(self) -> Dict[str, Any]:
        """
        Get list of available avatars.
        
        Returns:
            Dict containing available avatars
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/avatar/list",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("Failed to get HeyGen avatars", 
                        status_code=e.response.status_code)
            raise Exception(f"Failed to get avatars: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error getting avatars", error=str(e))
            raise Exception(f"Failed to get avatars: {str(e)}")
    
    async def list_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices.
        
        Returns:
            Dict containing available voices
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/voice/list",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("Failed to get HeyGen voices", 
                        status_code=e.response.status_code)
            raise Exception(f"Failed to get voices: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error getting voices", error=str(e))
            raise Exception(f"Failed to get voices: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Check if the HeyGen API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/avatar/list",
                    headers=self.headers
                )
                return response.status_code == 200
        except:
            return False