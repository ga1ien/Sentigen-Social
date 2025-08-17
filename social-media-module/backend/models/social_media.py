"""
Pydantic models for social media posting functionality.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator


class SupportedPlatform(str, Enum):
    """Supported social media platforms."""

    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    BLUESKY = "bluesky"
    PINTEREST = "pinterest"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class PostStatus(str, Enum):
    """Status of a social media post."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    FAILED = "failed"


class SocialMediaPostRequest(BaseModel):
    """Request model for creating a social media post."""

    post: Optional[str] = Field(
        None,
        description="The text content of the post. Required unless using randomPost.",
        max_length=2200,  # Twitter's max length
    )

    platforms: List[SupportedPlatform] = Field(
        ..., description="List of social media platforms to post to", min_items=1
    )

    media_urls: Optional[List[HttpUrl]] = Field(
        None, alias="media_urls", description="URLs of images or videos to include in the post", max_items=10
    )

    # Scheduling options
    schedule_date: Optional[datetime] = Field(
        None, alias="schedule_date", description="Schedule the post for a future date/time"
    )

    # Testing options
    random_post: Optional[bool] = Field(False, alias="random_post", description="Use a random quote for testing")

    random_media_url: Optional[bool] = Field(
        False, alias="random_media_url", description="Use a random image/video for testing"
    )

    is_landscape_video: Optional[bool] = Field(
        False, alias="is_landscape_video", description="Use landscape video format"
    )

    is_portrait_video: Optional[bool] = Field(
        False, alias="is_portrait_video", description="Use portrait video format (required for TikTok/Reels)"
    )

    # Platform-specific options
    platform_options: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, alias="platform_options", description="Platform-specific posting options"
    )

    # Hashtags and mentions
    hashtags: Optional[List[str]] = Field(None, description="List of hashtags to include", max_items=30)

    mentions: Optional[List[str]] = Field(None, description="List of usernames to mention")

    @validator("post")
    def validate_post_content(cls, v, values):
        """Validate that either post content or randomPost is provided."""
        if not v and not values.get("random_post", False):
            raise ValueError("Either post content or randomPost must be provided")
        return v

    @validator("hashtags")
    def validate_hashtags(cls, v):
        """Ensure hashtags start with # symbol."""
        if v:
            return [tag if tag.startswith("#") else f"#{tag}" for tag in v]
        return v

    @validator("mentions")
    def validate_mentions(cls, v):
        """Ensure mentions start with @ symbol."""
        if v:
            return [mention if mention.startswith("@") else f"@{mention}" for mention in v]
        return v

    class Config:
        """Pydantic configuration."""

        allow_population_by_field_name = True
        use_enum_values = True


class PlatformResult(BaseModel):
    """Result for a single platform posting attempt."""

    platform: SupportedPlatform = Field(..., description="The social media platform")

    status: PostStatus = Field(..., description="Status of the post on this platform")

    post_id: Optional[str] = Field(None, alias="id", description="Platform-specific post ID")

    post_url: Optional[HttpUrl] = Field(None, alias="post_url", description="Direct URL to view the post")

    error_message: Optional[str] = Field(None, alias="error_message", description="Error message if posting failed")

    used_quota: Optional[int] = Field(None, alias="used_quota", description="API quota used for this post")

    additional_info: Optional[Dict[str, Any]] = Field(
        None, alias="additional_info", description="Additional platform-specific information"
    )

    class Config:
        """Pydantic configuration."""

        allow_population_by_field_name = True
        use_enum_values = True


class SocialMediaPostResponse(BaseModel):
    """Response model for social media post creation."""

    status: PostStatus = Field(..., description="Overall status of the posting operation")

    message: str = Field(..., description="Human-readable message about the operation")

    post_id: Optional[str] = Field(None, alias="id", description="Unique identifier for this posting operation")

    ref_id: Optional[str] = Field(None, alias="ref_id", description="Reference ID from Ayrshare")

    post_content: Optional[str] = Field(None, alias="post", description="The actual content that was posted")

    platform_results: List[PlatformResult] = Field(
        default_factory=list, alias="post_ids", description="Results for each platform"
    )

    errors: List[str] = Field(default_factory=list, description="List of error messages if any occurred")

    created_at: datetime = Field(
        default_factory=datetime.utcnow, alias="created_at", description="Timestamp when the post was created"
    )

    scheduled_for: Optional[datetime] = Field(
        None, alias="scheduled_for", description="Scheduled posting time if applicable"
    )

    class Config:
        """Pydantic configuration."""

        allow_population_by_field_name = True
        use_enum_values = True


class SocialMediaAnalyticsRequest(BaseModel):
    """Request model for getting post analytics."""

    post_id: str = Field(..., description="The post ID to get analytics for")

    platforms: Optional[List[SupportedPlatform]] = Field(None, description="Specific platforms to get analytics for")


class SocialMediaAnalyticsResponse(BaseModel):
    """Response model for post analytics."""

    post_id: str = Field(..., description="The post ID")

    analytics: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Analytics data per platform")

    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="When the analytics were retrieved")


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str = Field(default="healthy", description="Service health status")

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")

    version: str = Field(default="1.0.0", description="API version")

    ayrshare_connected: bool = Field(default=False, description="Whether Ayrshare API is accessible")

    heygen_connected: bool = Field(default=False, description="Whether HeyGen API is accessible")

    services: Dict[str, bool] = Field(default_factory=dict, description="Status of individual services")
