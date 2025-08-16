"""
Ayrshare API client for social media posting.
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


class AyrshareClient:
    """
    Async client for interacting with the Ayrshare API.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Ayrshare client.
        
        Args:
            api_key: Ayrshare API key. If None, will use AYRSHARE_API_KEY env var.
            base_url: Ayrshare API base URL. If None, will use AYRSHARE_BASE_URL env var.
        """
        self.api_key = api_key or os.getenv("AYRSHARE_API_KEY")
        self.base_url = base_url or os.getenv("AYRSHARE_BASE_URL", "https://api.ayrshare.com/api")
        
        if not self.api_key:
            raise ValueError("Ayrshare API key is required. Set AYRSHARE_API_KEY environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def post_to_social_media(
        self,
        post_content: Optional[str] = None,
        platforms: List[str] = None,
        media_urls: Optional[List[str]] = None,
        schedule_date: Optional[datetime] = None,
        random_post: bool = False,
        random_media_url: bool = False,
        is_landscape_video: bool = False,
        is_portrait_video: bool = False,
        platform_options: Optional[Dict[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Post content to social media platforms via Ayrshare API.
        
        Args:
            post_content: The text content to post
            platforms: List of platform names to post to
            media_urls: List of media URLs to include
            schedule_date: When to schedule the post
            random_post: Use random post content for testing
            random_media_url: Use random media for testing
            is_landscape_video: Use landscape video format
            is_portrait_video: Use portrait video format
            platform_options: Platform-specific options
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the API response
        """
        if not platforms:
            raise ValueError("At least one platform must be specified")
        
        # Build the request payload
        payload = {
            "platforms": platforms
        }
        
        # Add post content
        if random_post:
            payload["randomPost"] = True
        elif post_content:
            payload["post"] = post_content
        else:
            raise ValueError("Either post_content or random_post must be provided")
        
        # Add media options
        if media_urls:
            payload["mediaUrls"] = media_urls
        elif random_media_url:
            payload["randomMediaUrl"] = True
            
        if is_landscape_video:
            payload["isLandscapeVideo"] = True
        if is_portrait_video:
            payload["isPortraitVideo"] = True
        
        # Add scheduling
        if schedule_date:
            payload["scheduleDate"] = schedule_date.isoformat()
        
        # Add platform-specific options
        if platform_options:
            for platform, options in platform_options.items():
                payload[f"{platform}Options"] = options
        
        # Add any additional parameters
        payload.update(kwargs)
        
        logger.info("Posting to social media", platforms=platforms, has_media=bool(media_urls or random_media_url))
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/post",
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info("Social media post successful", 
                           status=result.get("status"), 
                           post_id=result.get("id"))
                
                return result
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                error_detail = error_response.get("message", str(e))
            except:
                error_detail = str(e)
            
            logger.error("Ayrshare API error", 
                        status_code=e.response.status_code,
                        error=error_detail)
            
            raise Exception(f"Ayrshare API error ({e.response.status_code}): {error_detail}")
            
        except Exception as e:
            logger.error("Unexpected error posting to social media", error=str(e))
            raise Exception(f"Failed to post to social media: {str(e)}")
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific post.
        
        Args:
            post_id: The post ID to get analytics for
            
        Returns:
            Dict containing analytics data
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/analytics/post/{post_id}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("Failed to get post analytics", 
                        post_id=post_id,
                        status_code=e.response.status_code)
            raise Exception(f"Failed to get analytics: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error getting analytics", error=str(e))
            raise Exception(f"Failed to get analytics: {str(e)}")
    
    async def get_connected_accounts(self) -> Dict[str, Any]:
        """
        Get list of connected social media accounts.
        
        Returns:
            Dict containing connected accounts information
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/profiles",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("Failed to get connected accounts", 
                        status_code=e.response.status_code)
            raise Exception(f"Failed to get connected accounts: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error getting connected accounts", error=str(e))
            raise Exception(f"Failed to get connected accounts: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Check if the Ayrshare API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use a simple POST test instead of profiles (which requires Business Plan)
                response = await client.post(
                    f"{self.base_url}/post",
                    json={"post": "health check", "platforms": ["test"], "validate": True},
                    headers=self.headers
                )
                # API is accessible if we get any response (even errors about platforms)
                return response.status_code in [200, 400]
        except:
            return False