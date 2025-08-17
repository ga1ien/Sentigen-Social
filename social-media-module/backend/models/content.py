"""
Content models for the social media platform.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Content type enumeration."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


class Platform(str, Enum):
    """Social media platform enumeration."""

    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class PostStatus(str, Enum):
    """Post status enumeration."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class AIProvider(str, Enum):
    """AI provider enumeration."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    MIDJOURNEY = "midjourney"
    HEYGEN = "heygen"
    VEO3 = "veo3"


# Content Generation Models
class ContentGenerationRequest(BaseModel):
    """Request model for AI content generation."""

    prompt: str = Field(..., description="Content generation prompt")
    content_type: ContentType = Field(default=ContentType.TEXT, description="Type of content to generate")
    platforms: List[Platform] = Field(default=[], description="Target platforms for optimization")
    tone: Optional[str] = Field(default="professional", description="Tone of voice")
    length: Optional[str] = Field(default="medium", description="Content length (short, medium, long)")
    include_hashtags: bool = Field(default=True, description="Include relevant hashtags")
    include_emojis: bool = Field(default=False, description="Include emojis")
    ai_provider: AIProvider = Field(default=AIProvider.ANTHROPIC, description="AI provider to use")
    additional_context: Optional[str] = Field(default=None, description="Additional context for generation")


class ContentVariation(BaseModel):
    """Content variation model."""

    id: UUID = Field(default_factory=uuid4)
    content: str = Field(..., description="Generated content")
    platform: Optional[Platform] = Field(default=None, description="Platform-specific optimization")
    character_count: int = Field(..., description="Character count")
    hashtags: List[str] = Field(default=[], description="Extracted hashtags")
    mentions: List[str] = Field(default=[], description="Extracted mentions")
    confidence_score: Optional[float] = Field(default=None, description="AI confidence score")


class ContentGenerationResponse(BaseModel):
    """Response model for AI content generation."""

    request_id: UUID = Field(default_factory=uuid4)
    variations: List[ContentVariation] = Field(..., description="Generated content variations")
    ai_provider: AIProvider = Field(..., description="AI provider used")
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    cost_usd: Optional[float] = Field(default=None, description="Generation cost")


# Media Models
class MediaAsset(BaseModel):
    """Media asset model."""

    id: UUID = Field(default_factory=uuid4)
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    storage_url: str = Field(..., description="Storage URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")
    width: Optional[int] = Field(default=None, description="Image/video width")
    height: Optional[int] = Field(default=None, description="Image/video height")
    duration_seconds: Optional[int] = Field(default=None, description="Video duration")
    generated_by: Optional[AIProvider] = Field(default=None, description="AI provider that generated this asset")
    generation_params: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")
    alt_text: Optional[str] = Field(default=None, description="Alt text for accessibility")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MediaUploadRequest(BaseModel):
    """Media upload request model."""

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    alt_text: Optional[str] = Field(default=None, description="Alt text for accessibility")


# Post Models
class SocialMediaPost(BaseModel):
    """Social media post model."""

    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID = Field(..., description="Workspace ID")
    user_id: UUID = Field(..., description="User ID")
    content: str = Field(..., description="Post content")
    content_type: ContentType = Field(default=ContentType.TEXT)
    platforms: List[Platform] = Field(default=[], description="Target platforms")
    media_assets: List[UUID] = Field(default=[], description="Attached media asset IDs")
    status: PostStatus = Field(default=PostStatus.DRAFT)
    scheduled_at: Optional[datetime] = Field(default=None, description="Scheduled publish time")
    published_at: Optional[datetime] = Field(default=None, description="Actual publish time")

    # Platform-specific data
    platform_posts: Dict[Platform, Dict[str, Any]] = Field(
        default_factory=dict, description="Platform-specific post data"
    )

    # Analytics
    analytics: Dict[str, Any] = Field(default_factory=dict, description="Post analytics")

    # Metadata
    tags: List[str] = Field(default=[], description="Content tags")
    campaign_id: Optional[UUID] = Field(default=None, description="Campaign ID")
    ai_generated: bool = Field(default=False, description="Whether content was AI-generated")
    ai_provider: Optional[AIProvider] = Field(default=None, description="AI provider used")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PostCreateRequest(BaseModel):
    """Request model for creating a post."""

    content: str = Field(..., description="Post content")
    content_type: ContentType = Field(default=ContentType.TEXT)
    platforms: List[Platform] = Field(..., description="Target platforms")
    media_asset_ids: List[UUID] = Field(default=[], description="Media asset IDs")
    scheduled_at: Optional[datetime] = Field(default=None, description="Schedule time")
    tags: List[str] = Field(default=[], description="Content tags")
    campaign_id: Optional[UUID] = Field(default=None, description="Campaign ID")


class PostUpdateRequest(BaseModel):
    """Request model for updating a post."""

    content: Optional[str] = Field(default=None, description="Post content")
    platforms: Optional[List[Platform]] = Field(default=None, description="Target platforms")
    media_asset_ids: Optional[List[UUID]] = Field(default=None, description="Media asset IDs")
    scheduled_at: Optional[datetime] = Field(default=None, description="Schedule time")
    status: Optional[PostStatus] = Field(default=None, description="Post status")
    tags: Optional[List[str]] = Field(default=None, description="Content tags")


class PostResponse(BaseModel):
    """Response model for post operations."""

    post: SocialMediaPost = Field(..., description="Post data")
    media_assets: List[MediaAsset] = Field(default=[], description="Associated media assets")


class PostListResponse(BaseModel):
    """Response model for post listing."""

    posts: List[SocialMediaPost] = Field(..., description="List of posts")
    total: int = Field(..., description="Total number of posts")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Posts per page")
    has_next: bool = Field(..., description="Whether there are more pages")


# Analytics Models
class EngagementMetrics(BaseModel):
    """Engagement metrics model."""

    views: int = Field(default=0)
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    shares: int = Field(default=0)
    clicks: int = Field(default=0)
    saves: int = Field(default=0)
    engagement_rate: float = Field(default=0.0, description="Engagement rate percentage")


class PlatformAnalytics(BaseModel):
    """Platform-specific analytics model."""

    platform: Platform = Field(..., description="Social media platform")
    post_id: str = Field(..., description="Platform-specific post ID")
    metrics: EngagementMetrics = Field(..., description="Engagement metrics")
    reach: int = Field(default=0, description="Post reach")
    impressions: int = Field(default=0, description="Post impressions")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PostAnalytics(BaseModel):
    """Complete post analytics model."""

    post_id: UUID = Field(..., description="Internal post ID")
    platforms: List[PlatformAnalytics] = Field(default=[], description="Platform-specific analytics")
    total_metrics: EngagementMetrics = Field(..., description="Aggregated metrics")
    performance_score: float = Field(default=0.0, description="Overall performance score")
    best_performing_platform: Optional[Platform] = Field(default=None)


# Campaign Models
class Campaign(BaseModel):
    """Campaign model."""

    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID = Field(..., description="Workspace ID")
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(default=None, description="Campaign description")
    start_date: datetime = Field(..., description="Campaign start date")
    end_date: Optional[datetime] = Field(default=None, description="Campaign end date")
    platforms: List[Platform] = Field(default=[], description="Target platforms")
    tags: List[str] = Field(default=[], description="Campaign tags")
    budget_usd: Optional[float] = Field(default=None, description="Campaign budget")
    status: str = Field(default="active", description="Campaign status")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Workspace Models
class Workspace(BaseModel):
    """Workspace model."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Workspace name")
    description: Optional[str] = Field(default=None, description="Workspace description")
    owner_id: UUID = Field(..., description="Owner user ID")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Workspace settings")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceCreateRequest(BaseModel):
    """Request model for creating a workspace."""

    name: str = Field(..., description="Workspace name")
    description: Optional[str] = Field(default=None, description="Workspace description")


# User Models
class User(BaseModel):
    """User model."""

    id: UUID = Field(default_factory=uuid4)
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(default=None, description="Full name")
    avatar_url: Optional[str] = Field(default=None, description="Avatar URL")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# API Response Models
class APIResponse(BaseModel):
    """Generic API response model."""

    success: bool = Field(default=True)
    message: Optional[str] = Field(default=None)
    data: Optional[Any] = Field(default=None)
    errors: Optional[List[str]] = Field(default=None)


class PaginatedResponse(BaseModel):
    """Paginated response model."""

    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
